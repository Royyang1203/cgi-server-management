# services/server_state_monitor_service.py
from datetime import datetime, UTC
from models.server import Server
from models.database import db
from services.schedule_service import ScheduleService
from services.power_control_service import PowerControlService
import logging
import requests

logger = logging.getLogger(__name__)

class ServerStateMonitorService:
    INFLUXDB_URL = 'https://influxdb.cgi.lab.nycu.edu.tw/query'
    INFLUXDB_DB = 'telegraf'
    IDLE_THRESHOLD = 5.0  # 5% threshold for CPU and GPU usage
    
    @staticmethod
    def query_influxdb(query, timeout=10):
        """Query InfluxDB using direct HTTP request with timeout"""
        url = f"{ServerStateMonitorService.INFLUXDB_URL}?db={ServerStateMonitorService.INFLUXDB_DB}"
        params = {
            'q': query,
            'epoch': 'ms'
        }
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"InfluxDB query failed: {str(e)}")
            return None

    @staticmethod
    def get_server_resource_usage(server_name):
        """Get CPU and GPU usage for a specific server
        
        Args:
            server_name (str): Name of the server to check
            
        Returns:
            dict: Server resource usage data including CPU and GPU metrics
        """
        try:
            # Query CPU usage
            cpu_query = f'''
            SELECT usage_idle, usage_system, usage_user 
            FROM "cpu" 
            WHERE "cpu" = 'cpu-total' AND "host" = '{server_name}'
            AND time > now() - 5m 
            ORDER BY time DESC 
            LIMIT 1
            '''
            cpu_results = ServerStateMonitorService.query_influxdb(cpu_query)
            
            # Query GPU usage
            gpu_query = f'''
            SELECT utilization_gpu
            FROM "nvidia_smi"
            WHERE "host" = '{server_name}'
            AND time > now() - 5m
            ORDER BY time DESC
            LIMIT 1
            '''
            gpu_results = ServerStateMonitorService.query_influxdb(gpu_query)
            
            usage_data = {
                'cpu_usage': None,
                'gpu_usage': None,
                'has_data': False
            }
            
            # Process CPU data
            if (cpu_results and 'results' in cpu_results and 
                cpu_results['results'][0].get('series')):
                series = cpu_results['results'][0]['series'][0]
                values = series['values'][0]
                columns = series['columns']
                data = dict(zip(columns, values))
                usage_data['cpu_usage'] = 100 - data['usage_idle']  # Convert idle to usage
                usage_data['has_data'] = True
            
            # Process GPU data
            if (gpu_results and 'results' in gpu_results and 
                gpu_results['results'][0].get('series')):
                series = gpu_results['results'][0]['series'][0]
                values = series['values'][0]
                columns = series['columns']
                data = dict(zip(columns, values))
                usage_data['gpu_usage'] = data['utilization_gpu']
            
            return usage_data
            
        except Exception as e:
            logger.error(f"Error getting resource usage for {server_name}: {str(e)}")
            return None
    
    @staticmethod
    def _check_idle_state(server):
        """Check if a server is in idle state based on CPU and GPU usage
        
        Returns:
            bool: True if server is idle, False if server is in use
        """
        try:
            usage_data = ServerStateMonitorService.get_server_resource_usage(server.name)
            
            if not usage_data or not usage_data['has_data']:
                logger.warning(f"No resource usage data available for {server.name}")
                return server.is_idle  # Keep current state if no data
            
            cpu_idle = usage_data['cpu_usage'] < ServerStateMonitorService.IDLE_THRESHOLD
            
            # For servers with GPU, check both CPU and GPU
            if usage_data['gpu_usage'] is not None:
                gpu_idle = usage_data['gpu_usage'] < ServerStateMonitorService.IDLE_THRESHOLD
                is_idle = cpu_idle and gpu_idle
                logger.info(f"Server {server.name} status - CPU: {usage_data['cpu_usage']:.1f}%, "
                          f"GPU: {usage_data['gpu_usage']:.1f}%, Idle: {is_idle}")
            else:
                # For CPU-only servers, check only CPU
                is_idle = cpu_idle
                logger.info(f"Server {server.name} status - CPU: {usage_data['cpu_usage']:.1f}%, "
                          f"Idle: {is_idle}")
            
            return is_idle, usage_data
            
        except Exception as e:
            logger.error(f"Failed to check idle state for {server.name}: {str(e)}")
            return server.is_idle, None  # Return current recorded state if check fails
    
    @staticmethod
    def check_and_update_server_states():
        """Check and update the status of all servers"""
        servers = Server.query.all()
        now = datetime.now(UTC)  # Ensure UTC time
        
        for server in servers:
            try:
                # Check power state
                power_state = ServerStateMonitorService._check_power_state(server)
                if power_state != server.power_state:
                    server.power_state = power_state
                    server.last_update_time = now
                    logger.info(f"Server {server.name} power state updated to {power_state}")
                
                # Only check idle state and resource usage if server is powered on
                if power_state == 'ON':
                    is_idle, usage_data = ServerStateMonitorService._check_idle_state(server)
                    
                    # Update idle state
                    if is_idle and not server.is_idle:
                        server.is_idle = True
                        server.idle_start_time = now  # Ensure UTC time
                        logger.info(f"Server {server.name} marked as idle")
                    elif not is_idle and server.is_idle:
                        server.is_idle = False
                        server.idle_start_time = None
                        logger.info(f"Server {server.name} no longer idle")
                    
                    # Update resource usage in database
                    if usage_data and usage_data['has_data']:
                        server.cpu_usage = round(usage_data['cpu_usage'], 2) if usage_data['cpu_usage'] is not None else None
                        server.gpu_usage = round(usage_data['gpu_usage'], 2) if usage_data['gpu_usage'] is not None else None
                        logger.info(f"Updated resource usage for {server.name} - CPU: {server.cpu_usage}%, GPU: {server.gpu_usage}%")
                else:
                    # If server is off, clear resource usage
                    server.cpu_usage = None
                    server.gpu_usage = None
                    server.is_idle = False
                    server.idle_start_time = None
                
                db.session.commit()
            except Exception as e:
                logger.error(f"Error updating state for server {server.name}: {str(e)}")
                db.session.rollback()
    
    @staticmethod
    def _check_power_state(server):
        """Check the power state of a server
        
        Returns:
            str: 'ON' or 'OFF'
        """
        try:
            return PowerControlService.get_power_status(server)
        except Exception as e:
            logger.error(f"Failed to check power state for {server.name}: {str(e)}")
            return server.power_state  # Return current recorded state if check fails
    
    @staticmethod
    def _calculate_idle_duration(idle_start_time):
        """Calculate idle duration in minutes
        
        Args:
            idle_start_time: The time when the server became idle
            
        Returns:
            int: Duration in minutes, or 0 if start time is None
        """
        if not idle_start_time:
            return 0
            
        now = datetime.now(UTC)
        if idle_start_time.tzinfo is None:
            idle_start_time = idle_start_time.replace(tzinfo=UTC)
            
        return round((now - idle_start_time).total_seconds() / 60.0)
    
    @staticmethod
    def check_idle_and_shutdown():
        """Check idle servers and shut them down if conditions are met"""
        logger.info("Starting idle server check for automatic shutdown...")
        
        # Get all servers that have auto shutdown enabled, are powered on and idle
        servers = Server.query.filter_by(
            power_state='ON',
            is_idle=True,
            auto_shutdown_enabled=True
        ).all()
        
        logger.info(f"Found {len(servers)} powered on, idle servers with auto shutdown enabled")
        
        now = datetime.now(UTC)
        for server in servers:
            try:
                logger.info(f"Checking server {server.name} (idle threshold: {server.idle_threshold_mins} minutes)")
                
                # Calculate idle duration
                idle_duration = ServerStateMonitorService._calculate_idle_duration(server.idle_start_time)
                logger.info(f"Server {server.name} has been idle for {idle_duration} minutes")
                
                if idle_duration >= server.idle_threshold_mins:
                    logger.info(f"Server {server.name} exceeded idle threshold ({idle_duration}/{server.idle_threshold_mins} minutes)")
                    
                    # Check if server is in no-shutdown schedule
                    if not ScheduleService.is_in_schedule(server, now):
                        logger.info(f"Initiating shutdown for server {server.name}")
                        PowerControlService.shutdown(server)
                        logger.info(f"Shutdown command sent to server {server.name}")
                    else:
                        logger.info(f"Server {server.name} is in no-shutdown schedule, skipping shutdown")
                else:
                    logger.info(f"Server {server.name} has not reached idle threshold yet ({idle_duration}/{server.idle_threshold_mins} minutes)")
            except Exception as e:
                logger.error(f"Error processing server {server.name}: {str(e)}")
                continue
        
        logger.info("Completed idle server check")
