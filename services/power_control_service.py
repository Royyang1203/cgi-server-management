# services/power_control_service.py
import subprocess
from datetime import datetime, UTC
from models.database import db

class PowerControlService:
    
    @staticmethod
    def _run_ipmi_command(server, action):
        """
        Execute IPMI command
        """
        command = [
            "ipmitool", "-I", "lanplus",
            "-H", server.ipmi_host,
            "-U", server.ipmi_user,
            "-P", server.ipmi_pass,
            "chassis", "power", action
        ]
        
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, str(e)

    @staticmethod
    def get_power_status(server):
        """
        Get server power status
        """
        success, output = PowerControlService._run_ipmi_command(server, "status")
        if success:
            # Update database status
            if "on" in output.lower():
                server.power_state = "ON"
            elif "off" in output.lower():
                server.power_state = "OFF"
            server.last_update_time = datetime.now(UTC)
            db.session.commit()
            return server.power_state
        return "UNKNOWN"

    @staticmethod
    def startup(server):
        """
        Power on the server
        """
        success, _ = PowerControlService._run_ipmi_command(server, "on")
        if success:
            server.power_state = "ON"
            server.last_update_time = datetime.now(UTC)
            # Reset idle state
            server.is_idle = True
            server.idle_start_time = datetime.now(UTC)
            db.session.commit()
        return success

    @staticmethod
    def shutdown(server):
        """
        Power off the server
        """
        success, _ = PowerControlService._run_ipmi_command(server, "off")
        if success:
            server.power_state = "OFF"
            server.last_update_time = datetime.now(UTC)
            db.session.commit()
        return success
