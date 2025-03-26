# models/server.py
from datetime import datetime, UTC
from models.database import db

class Server(db.Model):
    __tablename__ = 'servers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    ipmi_host = db.Column(db.String(100), nullable=False)
    ipmi_user = db.Column(db.String(100), nullable=False)
    ipmi_pass = db.Column(db.String(100), nullable=False)
    power_state = db.Column(db.String(20), default='OFF')
    last_update_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Idle monitoring fields
    is_idle = db.Column(db.Boolean, default=False)
    idle_start_time = db.Column(db.DateTime, nullable=True)
    idle_threshold_mins = db.Column(db.Integer, default=30)  # Default 30 minutes idle threshold
    cpu_usage = db.Column(db.Float, nullable=True)
    gpu_usage = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<Server id={self.id} name={self.name}>"
