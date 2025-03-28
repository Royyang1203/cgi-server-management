# routes.py
from flask import Blueprint, jsonify, request
from flask_restx import Api, Resource, fields
from controllers.server_controller import ServerController
from controllers.server_management_controller import ServerManagementController
from models.server import Server
from models.database import db

# Create Blueprint
routes_bp = Blueprint('routes', __name__)

# Create API instance
api = Api(routes_bp,
    title='Server Management API',
    version='1.0',
    description='API for managing and controlling servers via IPMI',
    doc='/docs'  # Swagger UI will be available at /api/docs
)

# Define namespaces
server_ns = api.namespace('servers', description='Server operations')
manage_ns = api.namespace('servers/manage', description='Server management operations')

# Define nested model for resource usage
resource_usage_model = api.model('ResourceUsage', {
    'cpu_usage': fields.Float(description='Current CPU usage percentage'),
    'gpu_usage': fields.Float(description='Current GPU usage percentage')
})

# Define models for documentation
server_model = api.model('Server', {
    'id': fields.Integer(description='Server identifier'),
    'name': fields.String(description='Server name'),
    'ipmi_host': fields.String(description='IPMI host address'),
    'power_state': fields.String(description='Current power state'),
    'last_update_time': fields.DateTime(dt_format='iso8601', description='Last status update time'),
    'is_idle': fields.Boolean(description='Whether the server is currently idle'),
    'idle_start_time': fields.DateTime(dt_format='iso8601', description='Time when the server became idle'),
    'idle_duration_mins': fields.Integer(description='Duration of current idle state in minutes'),
    'idle_threshold_mins': fields.Integer(description='Threshold in minutes before idle server is shut down'),
    'current_usage': fields.Nested(resource_usage_model, description='Current resource usage information')
})

power_response = api.model('PowerResponse', {
    'success': fields.Boolean(description='Operation success status'),
    'message': fields.String(description='Response message')
})

error_response = api.model('ErrorResponse', {
    'message': fields.String(description='Error message')
})

server_create_model = api.model('ServerCreate', {
    'name': fields.String(required=True, description='Server name'),
    'ipmi_host': fields.String(required=True, description='IPMI host address'),
    'ipmi_user': fields.String(required=True, description='IPMI username'),
    'ipmi_pass': fields.String(required=True, description='IPMI password')
})

server_update_model = api.model('ServerUpdate', {
    'ipmi_host': fields.String(description='IPMI host address'),
    'ipmi_user': fields.String(description='IPMI username'),
    'ipmi_pass': fields.String(description='IPMI password')
})

# Server listing and status endpoints
@server_ns.route('')
class ServerList(Resource):
    @server_ns.doc('list_servers')
    @server_ns.marshal_with(server_model, as_list=True)
    def get(self):
        """List all servers"""
        return ServerController.get_all()

@server_ns.route('/<int:server_id>/status')
@server_ns.param('server_id', 'The server identifier')
class ServerStatusById(Resource):
    @server_ns.doc('get_server_status')
    @server_ns.marshal_with(server_model)
    @server_ns.response(404, 'Server not found', error_response)
    def get(self, server_id):
        """Get server status by ID"""
        return ServerController.get_status(server_id)

@server_ns.route('/name/<string:server_name>/status')
@server_ns.param('server_name', 'The server name')
class ServerStatusByName(Resource):
    @server_ns.doc('get_server_status_by_name')
    @server_ns.marshal_with(server_model)
    @server_ns.response(404, 'Server not found', error_response)
    def get(self, server_name):
        """Get server status by name"""
        return ServerController.get_status_by_name(server_name)

# Server power control endpoints
@server_ns.route('/<int:server_id>/power/<string:action>')
@server_ns.param('server_id', 'The server identifier')
@server_ns.param('action', 'Power action (on/off)')
class ServerPowerById(Resource):
    @server_ns.doc('power_control')
    @server_ns.response(200, 'Success', power_response)
    @server_ns.response(404, 'Server not found', error_response)
    @server_ns.response(500, 'Operation failed', power_response)
    def post(self, server_id, action):
        """Control server power by ID"""
        if action == 'on':
            return ServerController.power_on(server_id)
        elif action == 'off':
            return ServerController.power_off(server_id)
        else:
            api.abort(400, f"Invalid action: {action}")

@server_ns.route('/name/<string:server_name>/power/<string:action>')
@server_ns.param('server_name', 'The server name')
@server_ns.param('action', 'Power action (on/off)')
class ServerPowerByName(Resource):
    @server_ns.doc('power_control_by_name')
    @server_ns.response(200, 'Success', power_response)
    @server_ns.response(404, 'Server not found', error_response)
    @server_ns.response(500, 'Operation failed', power_response)
    def post(self, server_name, action):
        """Control server power by name"""
        if action == 'on':
            return ServerController.power_on_by_name(server_name)
        elif action == 'off':
            return ServerController.power_off_by_name(server_name)
        else:
            api.abort(400, f"Invalid action: {action}")

# Server management endpoints
@manage_ns.route('')
class ServerManagement(Resource):
    @manage_ns.doc('create_server')
    @manage_ns.expect(server_create_model)
    @manage_ns.marshal_with(server_model, code=201)
    def post(self):
        """Create a new server"""
        return ServerManagementController.create_server()

@manage_ns.route('/<string:server_name>')
@manage_ns.param('server_name', 'The server name')
class ServerManagementByName(Resource):
    @manage_ns.doc('update_server')
    @manage_ns.expect(server_update_model)
    @manage_ns.marshal_with(server_model)
    def put(self, server_name):
        """Update a server"""
        return ServerManagementController.update_server(server_name)

    @manage_ns.doc('delete_server')
    def delete(self, server_name):
        """Delete a server"""
        return ServerManagementController.delete_server(server_name)

@routes_bp.route('/servers/name/<server_name>/idle-settings', methods=['POST'])
def update_idle_settings(server_name):
    try:
        server = Server.query.filter_by(name=server_name).first()
        if not server:
            return jsonify({'success': False, 'message': 'Server not found'}), 404
        
        data = request.get_json()
        threshold = data.get('idle_threshold_mins')
        auto_shutdown = data.get('auto_shutdown_enabled')
        
        if threshold is not None:
            if not isinstance(threshold, int) or threshold < 1:
                return jsonify({'success': False, 'message': 'Invalid threshold value'}), 400
            server.idle_threshold_mins = threshold
            
        if auto_shutdown is not None:
            server.auto_shutdown_enabled = bool(auto_shutdown)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
