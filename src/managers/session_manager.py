from queue import Queue
from datetime import date
from src.managers.base_manager import BaseManager
from src.context.session_context import SessionContext
from src.models.session import Session
from src.api.task_types import get_task_dict, TaskType

class SessionManager(BaseManager):
    required_fields = {"SessionInfo", "WeekendInfo", "DriverInfo", "PlayerCarIdx"}

    def __init__(self, context: SessionContext, queue: Queue):
        super().__init__(context, queue)
        self.session_info = None
        self.weekend_info = None
        self.driver_info = None
        self.car_id = None
        self.session_sent = False

    def on_tick(self, telem, state):
        self.session_info = telem["SessionInfo"]
        self.weekend_info = telem["WeekendInfo"]
        self.driver_info = telem["DriverInfo"]
        self.car_id = telem["PlayerCarIdx"]

    def handle_event(self, event, telem, ctx):
        if event == "session_start" and not self.session_sent:
            self.set_context()
            self._send_session_info()
            self.session_sent = True
    
    def set_context(self):
        self.context.session_id = self.weekend_info["SubSessionID"]
        self.context.car_id = self.car_id

    def _send_session_info(self):
        car_info = self.driver_info["Drivers"][self.car_id]
        car_class_name = car_info["CarClassShortName"]
        car_name = car_info["CarScreenName"]

        data = Session(
            id=self.context.session_id,
            track=self.weekend_info["TrackDisplayName"],
            car_class=car_class_name if car_class_name else car_name,
            car=car_name,
            race_duration=self._get_race_duration(),
            session_date= date.today()
        )

        self.queue.put(get_task_dict(TaskType.SESSION, data))

    def _get_race_duration(self) -> float:
        sessions = self.session_info.get("Sessions", [])
        for s in sessions:
            if s["SessionType"] == "Race":
                return s["SessionTime"]
        return 0.0