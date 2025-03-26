# services/schedule_service.py
from models.schedule import Schedule
from datetime import datetime

class ScheduleService:

    @staticmethod
    def is_in_schedule(server, check_time: datetime) -> bool:
        schedules = server.schedules  # 根據 SQLAlchemy relationship 直接取
        for sch in schedules:
            if sch.start_time <= check_time <= sch.end_time:
                return True
        return False