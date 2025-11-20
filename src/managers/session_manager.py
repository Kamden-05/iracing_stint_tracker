from queue import Queue
from src.managers.base_manager import BaseManager

class SessionManager(BaseManager):
    required_fields = {"WeekendInfo", "DriverInfo"}
    
    def __init__(self, queue: Queue):
        super().__init__(queue)