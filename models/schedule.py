# models/schedule.py
from models.database import db
from datetime import datetime

class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    server = db.relationship('Server', backref='schedules')

    def __repr__(self):
        return f"<Schedule id={self.id} server_id={self.server_id}>"
