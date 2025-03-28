# app.py
import os
import logging
from flask import Flask, render_template
from flask_cors import CORS
from flask_apscheduler import APScheduler
from flask_migrate import Migrate
from flask_session import Session
from dotenv import load_dotenv

from models.database import db
from routes import routes_bp
from services.server_state_monitor_service import ServerStateMonitorService
from models.server import Server
from auth.routes import auth_bp, login_required
from config.config import config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    CORS(app)
    
    # Load config
    app.config.from_object(config[config_name])
    
    # Initialize Flask-Session
    Session(app)
    
    # Initialize database
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Register blueprints
    app.register_blueprint(routes_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Initialize scheduler
    scheduler = APScheduler()
    
    @scheduler.task('interval', id='monitor_servers', 
                   seconds=app.config['SERVER_MONITOR_INTERVAL'])
    def monitor_servers():
        with app.app_context():
            ServerStateMonitorService.check_and_update_server_states()
    
    # Main route for the web interface
    @app.route('/')
    def index():
        return render_template('login.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')
    
    scheduler.init_app(app)
    scheduler.start()
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
        server_count = Server.query.count()
        if server_count == 0:
            logger.info("No servers found in database. Please add servers through the API.")
    
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)  # Disabled reloader
