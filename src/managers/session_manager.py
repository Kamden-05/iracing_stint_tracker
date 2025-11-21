from queue import Queue
from datetime import date
from typing import Optional
from src.managers.base_manager import BaseManager
from src.context.race_context import RaceContext
from src.models.session import Session
from src.api.tasks import TaskType


class SessionManager(BaseManager):
    required_fields = {
        "SessionInfo": "session_info",
        "WeekendInfo": "weekend_info",
        "DriverInfo": "driver_info",
        "PlayerCarIdx": "car_id",
    }

    session_info: Optional[dict]
    weekend_info: Optional[dict]
    driver_info: Optional[dict]
    car_id: Optional[int]

    def __init__(self, context: RaceContext, queue: Queue):
        super().__init__(context, queue)

        for attr in self.required_fields.values():
            setattr(self, attr, None)

        self.session_sent = False

    def handle_event(self, event, telem, ctx):
        if event == "session_start" and not self.session_sent:
            self.set_context()
            self._post_session_info()
            self.session_sent = True

    def set_context(self):
        self.context.session_id = self.weekend_info["SubSessionID"]
        self.context.car_id = self.car_id

    def _post_session_info(self):
        car_info = self.driver_info["Drivers"][self.car_id]
        car_class_name = car_info["CarClassShortName"]
        car_name = car_info["CarScreenName"]

        data = Session(
            id=self.context.session_id,
            track=self.weekend_info["TrackDisplayName"],
            car_class=car_class_name if car_class_name else car_name,
            car=car_name,
            race_duration=self._get_race_duration(),
            session_date=date.today(),
        ).to_dict()

        self._send_data(TaskType.SESSION, data)

    def _get_race_duration(self) -> float:
        sessions = self.session_info.get("Sessions", [])
        for s in sessions:
            if s.get("SessionType") == "Race":
                return float(s["SessionTime"].split()[0])
        return 0.0
