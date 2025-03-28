from models.server import Server
from models.database import db
from datetime import datetime, UTC
from flask import Flask
from config.config import config
import os

def create_app(config_name='development'):
    """Create Flask application with the specified configuration."""
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(config[config_name])
    
    # Ensure instance folder exists
    try:
        os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create instance directory: {e}")
    
    # Initialize database with app
    db.init_app(app)
    
    return app

def init_nv_servers(start_num: int = 2, end_num: int = 29,
                   ipmi_user: str = "admin", ipmi_pass: str = "admin"):
    """
    Initialize NV servers in the database using the existing Server model
    """
    for num in range(start_num, end_num + 1):
        server_name = f"NV{num:02d}"
        ipmi_host = f"10.8.4.{num}"
        
        # Check if server already exists
        existing_server = Server.query.filter_by(name=server_name).first()
        if not existing_server:
            new_server = Server(
                name=server_name,
                ipmi_host=ipmi_host,
                ipmi_user=ipmi_user,
                ipmi_pass=ipmi_pass,
                power_state='OFF',
                last_update_time=datetime.now(UTC),
                is_idle=False,
                idle_threshold_mins=30,
                auto_shutdown_enabled=False
            )
            db.session.add(new_server)
    
    # Commit all changes
    db.session.commit()

def list_all_servers():
    """List all servers in the database"""
    servers = Server.query.order_by(Server.name).all()
    
    print("\nServer Database Contents:")
    print("-" * 70)
    for server in servers:
        print(f"Server: {server.name}")
        print(f"IPMI Host: {server.ipmi_host}")
        print(f"IPMI User: {server.ipmi_user}")
        print(f"Power State: {server.power_state}")
        print(f"Auto Shutdown: {'Enabled' if server.auto_shutdown_enabled else 'Disabled'}")
        print(f"Idle Threshold: {server.idle_threshold_mins} minutes")
        print("-" * 70)

def main():
    # Get config name from environment or use development as default
    config_name = os.getenv('FLASK_ENV', 'development')
    print(f"Using {config_name} configuration")
    
    # Create app with config
    app = create_app(config_name)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Initialize servers with default credentials
        init_nv_servers(
            start_num=3,
            end_num=29,
            ipmi_user="admin",  # Replace with your actual IPMI username
            ipmi_pass="admin"   # Replace with your actual IPMI password
        )
        
        # List all servers
        list_all_servers()

if __name__ == "__main__":
    main() 
