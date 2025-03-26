from influxdb import InfluxDBClient
import json
import requests
from datetime import datetime, timedelta

def query_influxdb(url, query, timeout=10):
    """
    Query InfluxDB using direct HTTP request with timeout
    """
    params = {
        'q': query,
        'epoch': 'ms'  # Get time in milliseconds
    }
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"Query timed out after {timeout} seconds: {query}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error during query: {e}")
        return None

def check_server_status(url, idle_threshold=5.0):
    """
    Get CPU and GPU usage data and check if servers are idle
    Returns a dictionary of server status
    """
    server_status = {}  # Store status for each host

    try:
        # Query CPU usage
        cpu_query = '''
        SELECT host, usage_idle, usage_system, usage_user 
        FROM "cpu" 
        WHERE "cpu" = 'cpu-total' AND time > now() - 5m 
        GROUP BY host 
        ORDER BY time DESC 
        LIMIT 1
        '''
        print("\n=== Querying CPU Usage ===")
        cpu_results = query_influxdb(url, cpu_query)

        if cpu_results and 'results' in cpu_results and cpu_results['results'][0].get('series'):
            print("\nCPU Usage by Host:")
            for series in cpu_results['results'][0]['series']:
                host = series['tags']['host']
                values = series['values'][0]
                columns = series['columns']
                data = dict(zip(columns, values))
                cpu_used = 100 - data['usage_idle']  # Convert idle to usage
                
                # Initialize host in status dict
                server_status[host] = {
                    'cpu_usage': cpu_used,
                    'gpu_usage': None,  # Will be updated if GPU exists
                    'is_idle': False,   # Will be updated after checking both CPU and GPU
                    'status_detail': []
                }
                
                print(f"{host}:")
                print(f"  Total CPU Usage: {cpu_used:.2f}%")
                print(f"  System: {data['usage_system']:.2f}%")
                print(f"  User: {data['usage_user']:.2f}%")

        # Query GPU usage
        gpu_query = '''
        SELECT host, utilization_gpu, memory_used, memory_total
        FROM "nvidia_smi"
        WHERE time > now() - 5m
        GROUP BY host
        ORDER BY time DESC
        LIMIT 1
        '''
        print("\n=== Querying GPU Usage ===")
        gpu_results = query_influxdb(url, gpu_query)

        if gpu_results and 'results' in gpu_results and gpu_results['results'][0].get('series'):
            print("\nGPU Usage by Host:")
            for series in gpu_results['results'][0]['series']:
                host = series['tags']['host']
                values = series['values'][0]
                columns = series['columns']
                data = dict(zip(columns, values))
                memory_used_gb = data['memory_used'] / 1024  # Convert to GB
                memory_total_gb = data['memory_total'] / 1024  # Convert to GB
                gpu_usage = data['utilization_gpu']
                
                if host in server_status:
                    server_status[host]['gpu_usage'] = gpu_usage
                else:
                    server_status[host] = {
                        'cpu_usage': None,
                        'gpu_usage': gpu_usage,
                        'is_idle': False,
                        'status_detail': []
                    }
                
                print(f"{host}:")
                print(f"  GPU Utilization: {gpu_usage:.1f}%")
                print(f"  Memory Usage: {memory_used_gb:.1f}GB / {memory_total_gb:.1f}GB")

        # Determine idle status for each server
        print("\n=== Server Status Summary ===")
        for host, status in server_status.items():
            status['status_detail'] = []
            
            # Check CPU usage
            if status['cpu_usage'] is not None:
                if status['cpu_usage'] < idle_threshold:
                    status['status_detail'].append(f"CPU idle ({status['cpu_usage']:.1f}% < {idle_threshold}%)")
                else:
                    status['status_detail'].append(f"CPU busy ({status['cpu_usage']:.1f}%)")
            
            # Check GPU usage if available
            if status['gpu_usage'] is not None:
                if status['gpu_usage'] < idle_threshold:
                    status['status_detail'].append(f"GPU idle ({status['gpu_usage']:.1f}% < {idle_threshold}%)")
                else:
                    status['status_detail'].append(f"GPU busy ({status['gpu_usage']:.1f}%)")
            
            # Server is idle only if both CPU and GPU are below threshold
            # For CPU-only servers, only check CPU
            if status['gpu_usage'] is not None:
                status['is_idle'] = (status['cpu_usage'] < idle_threshold and 
                                   status['gpu_usage'] < idle_threshold)
            else:
                status['is_idle'] = status['cpu_usage'] < idle_threshold
            
            # Print summary
            print(f"\n{host}:")
            print(f"  Idle: {'Yes' if status['is_idle'] else 'No'}")
            print(f"  Details: {', '.join(status['status_detail'])}")

        return server_status

    except Exception as e:
        print(f"Error checking server status: {e}")
        return None

def main():
    # Connection parameters
    base_url = 'https://influxdb.cgi.lab.nycu.edu.tw/query'
    database = 'telegraf'
    url_with_db = f'{base_url}?db={database}'

    try:
        # Check server status with 5% threshold
        server_status = check_server_status(url_with_db, idle_threshold=10.0)
        
        # Print available idle servers
        if server_status:
            idle_servers = [host for host, status in server_status.items() if status['is_idle']]
            print("\n=== Available Idle Servers ===")
            if idle_servers:
                print("The following servers are idle:")
                for server in idle_servers:
                    print(f"- {server}")
            else:
                print("No idle servers available at the moment.")

    except Exception as e:
        print(f"Error querying InfluxDB: {e}")

if __name__ == "__main__":
    main() 