# controllers/schedule_controller.py
from flask import request, jsonify
from models.server import Server
from models.schedule import Schedule
from models.database import db
from datetime import datetime

class ScheduleController:

    @staticmethod
    def get_schedules(server_id):
        server = Server.query.get(server_id)
        if not server:
            return jsonify({"message": "Server not found"}), 404
        
        schedules = server.schedules
        data = []
        for sch in schedules:
            data.append({
                "id": sch.id,
                "server_id": sch.server_id,
                "start_time": sch.start_time.isoformat(),
                "end_time": sch.end_time.isoformat(),
                "description": sch.description
            })
        return jsonify(data)

    @staticmethod
    def create_schedule(server_id):
        server = Server.query.get(server_id)
        if not server:
            return jsonify({"message": "Server not found"}), 404

        data = request.json
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
        description = data.get('description', '')

        schedule = Schedule(
            server_id = server.id,
            start_time = start_time,
            end_time = end_time,
            description = description
        )
        db.session.add(schedule)
        db.session.commit()
        return jsonify({"success": True, "data": {
            "id": schedule.id,
            "start_time": schedule.start_time.isoformat(),
            "end_time": schedule.end_time.isoformat(),
            "description": schedule.description
        }})

    @staticmethod
    def delete_schedule(server_id, schedule_id):
        schedule = Schedule.query.get(schedule_id)
        if not schedule or schedule.server_id != int(server_id):
            return jsonify({"message": "Schedule not found"}), 404
        
        db.session.delete(schedule)
        db.session.commit()
        return jsonify({"success": True})