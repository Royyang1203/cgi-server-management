from flask import request, jsonify
from models.server import Server
from models.database import db

class ServerManagementController:
    
    @staticmethod
    def create_server():
        """
        Create a new server in the database
        """
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'ipmi_host', 'ipmi_user', 'ipmi_pass']
        for field in required_fields:
            if field not in data:
                return jsonify({"message": f"Missing required field: {field}"}), 400
        
        # Check if server with same name already exists
        existing_server = Server.query.filter_by(name=data['name']).first()
        if existing_server:
            return jsonify({"message": f"Server with name '{data['name']}' already exists"}), 409
        
        # Create new server
        try:
            new_server = Server(
                name=data['name'],
                ipmi_host=data['ipmi_host'],
                ipmi_user=data['ipmi_user'],
                ipmi_pass=data['ipmi_pass']
            )
            db.session.add(new_server)
            db.session.commit()
            
            return jsonify({
                "message": "Server created successfully",
                "server": {
                    "id": new_server.id,
                    "name": new_server.name,
                    "ipmi_host": new_server.ipmi_host,
                    "power_state": new_server.power_state
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Failed to create server: {str(e)}"}), 500

    @staticmethod
    def update_server(server_name):
        """
        Update an existing server in the database
        """
        server = Server.query.filter_by(name=server_name).first()
        if not server:
            return jsonify({"message": f"Server '{server_name}' not found"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"message": "No update data provided"}), 400
        
        try:
            # Update only provided fields
            if 'ipmi_host' in data:
                server.ipmi_host = data['ipmi_host']
            if 'ipmi_user' in data:
                server.ipmi_user = data['ipmi_user']
            if 'ipmi_pass' in data:
                server.ipmi_pass = data['ipmi_pass']
            
            db.session.commit()
            
            return jsonify({
                "message": f"Server '{server_name}' updated successfully",
                "server": {
                    "id": server.id,
                    "name": server.name,
                    "ipmi_host": server.ipmi_host,
                    "power_state": server.power_state
                }
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Failed to update server: {str(e)}"}), 500

    @staticmethod
    def delete_server(server_name):
        """
        Delete a server from the database
        """
        server = Server.query.filter_by(name=server_name).first()
        if not server:
            return jsonify({"message": f"Server '{server_name}' not found"}), 404
        
        try:
            db.session.delete(server)
            db.session.commit()
            return jsonify({"message": f"Server '{server_name}' deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"Failed to delete server: {str(e)}"}), 500 