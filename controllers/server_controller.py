# controllers/server_controller.py
from flask import request
from models.server import Server
from models.database import db
from services.power_control_service import PowerControlService
from services.server_state_monitor_service import ServerStateMonitorService
from datetime import datetime, UTC

class ServerController:

    @staticmethod
    def get_all():
        servers = Server.query.all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "ipmi_host": s.ipmi_host,
                "power_state": s.power_state,
                "last_update_time": s.last_update_time,
                "is_idle": s.is_idle,
                "idle_start_time": s.idle_start_time,
                "idle_duration_mins": (
                    ServerController._calculate_idle_duration(s.idle_start_time)
                    if s.is_idle
                    else 0
                ),
                "idle_threshold_mins": s.idle_threshold_mins,
                "current_usage": {
                    "cpu_usage": s.cpu_usage,
                    "gpu_usage": s.gpu_usage
                }
            }
            for s in servers
        ]

    @staticmethod
    def _get_server_by_name(server_name):
        """
        Helper method to get server by name and handle not found case
        """
        server = Server.query.filter_by(name=server_name).first()
        if not server:
            return None, ({"message": f"Server '{server_name}' not found"}, 404)
        return server, None

    @staticmethod
    def _calculate_idle_duration(idle_start_time):
        """
        Calculate idle duration in minutes, handling timezone-aware and naive datetimes
        """
        if not idle_start_time:
            return 0
            
        # Convert idle_start_time to UTC if it's naive
        if idle_start_time.tzinfo is None:
            idle_start_time = idle_start_time.replace(tzinfo=UTC)
            
        now = datetime.now(UTC)
        return round((now - idle_start_time).total_seconds() / 60.0)

    @staticmethod
    def get_status(server_id):
        server = Server.query.get(server_id)
        if not server:
            return {"message": "Server not found"}, 404
        
        return {
            "id": server.id,
            "name": server.name,
            "ipmi_host": server.ipmi_host,
            "power_state": server.power_state,
            "last_update_time": server.last_update_time,
            "is_idle": server.is_idle,
            "idle_start_time": server.idle_start_time,
            "idle_duration_mins": (
                ServerController._calculate_idle_duration(server.idle_start_time)
                if server.is_idle
                else 0
            ),
            "idle_threshold_mins": server.idle_threshold_mins,
            "current_usage": {
                "cpu_usage": server.cpu_usage,
                "gpu_usage": server.gpu_usage
            }
        }

    @staticmethod
    def get_status_by_name(server_name):
        server, error = ServerController._get_server_by_name(server_name)
        if error:
            return error
        
        return {
            "id": server.id,
            "name": server.name,
            "ipmi_host": server.ipmi_host,
            "power_state": server.power_state,
            "last_update_time": server.last_update_time,
            "is_idle": server.is_idle,
            "idle_start_time": server.idle_start_time,
            "idle_duration_mins": (
                ServerController._calculate_idle_duration(server.idle_start_time)
                if server.is_idle
                else 0
            ),
            "idle_threshold_mins": server.idle_threshold_mins,
            "current_usage": {
                "cpu_usage": server.cpu_usage,
                "gpu_usage": server.gpu_usage
            }
        }
    
    @staticmethod
    def power_on(server_id):
        server = Server.query.get(server_id)
        if not server:
            return {"message": "Server not found"}, 404
        
        success = PowerControlService.startup(server)
        if success:
            return {"success": True, "message": "Server is powering on..."}
        return {"success": False, "message": "Failed to power on server"}, 500

    @staticmethod
    def power_on_by_name(server_name):
        server, error = ServerController._get_server_by_name(server_name)
        if error:
            return error
        
        success = PowerControlService.startup(server)
        if success:
            return {"success": True, "message": f"Server '{server_name}' is powering on..."}
        return {"success": False, "message": f"Failed to power on server '{server_name}'"}, 500

    @staticmethod
    def power_off(server_id):
        server = Server.query.get(server_id)
        if not server:
            return {"message": "Server not found"}, 404
        
        success = PowerControlService.shutdown(server)
        if success:
            return {"success": True, "message": "Server is shutting down..."}
        return {"success": False, "message": "Failed to power off server"}, 500

    @staticmethod
    def power_off_by_name(server_name):
        server, error = ServerController._get_server_by_name(server_name)
        if error:
            return error
        
        success = PowerControlService.shutdown(server)
        if success:
            return {"success": True, "message": f"Server '{server_name}' is shutting down..."}
        return {"success": False, "message": f"Failed to power off server '{server_name}'"}, 500
