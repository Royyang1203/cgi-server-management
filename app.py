# app.py
import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_apscheduler import APScheduler
from flask_migrate import Migrate

from models.database import db
from routes import routes_bp
from services.server_state_monitor_service import ServerStateMonitorService
from models.server import Server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "mydb.sqlite")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

logger.info(f"Database path: {db_path}")
logger.info(f"Database exists: {os.path.exists(db_path)}")

db.init_app(app)
migrate = Migrate(app, db)
app.register_blueprint(routes_bp, url_prefix='/api')

scheduler = APScheduler()

@scheduler.task('interval', id='monitor_servers', seconds=30)
def monitor_servers():
    with app.app_context():
        ServerStateMonitorService.check_and_update_server_states()

# @scheduler.task('interval', id='check_idle_servers', seconds=60)
# def check_idle_servers():
#     with app.app_context():
#         ServerStateMonitorService.check_idle_and_shutdown()

scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        server_count = Server.query.count()
        if server_count == 0:
            logger.info("No servers found in database. Please add servers through the API.")

    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)  # Disabled reloader
