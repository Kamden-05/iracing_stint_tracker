from queue import Queue
import threading
from src.fsm.driver_fsm import DriverFSM
from src.telemetry.iracing_client import IRacingClient
from src.telemetry.telemetry_loop import TelemetryLoop
from src.api.api_client import APIClient
from src.api.api_worker import APIWorker
from src.context.race_context import RaceContext
from src.managers.session_manager import SessionManager
from src.managers.stint_manager import StintManager
from src.managers.pitstop_manager import PitstopManager
from src.managers.lap_manager import LapManager


class AppEngine:
    def __init__(
        self,
        user_name: str,
        api_base_url: str,
    ):
        self.context = RaceContext(user_name=user_name)
        self.queue = Queue()
        self.stop_event = threading.Event()

        self.api_client = APIClient(api_base_url)
        self.api_worker = APIWorker(self.context, self.api_client, self.queue, self.stop_event)

        self.fsm = DriverFSM()
        self.managers = [
            SessionManager(self.context, self.queue),
            StintManager(self.context, self.queue),
        ]
        self.fsm.attach_managers(self.managers)

        self.telemetry_loop = TelemetryLoop(
            ir_client=IRacingClient(),
            fsm=self.fsm,
            user_name=user_name,
        )

        self.api_thread = threading.Thread(
            target=self.api_worker.run, daemon=True
        )
        self.telemetry_thread = threading.Thread(
            target=self.telemetry_loop.run, daemon=True
        )

    def start(self):
        print ("Starting API Worker")
        self.api_thread.start()

        print("Starting telemetry loop")
        self.telemetry_thread.start()

    def stop(self):
        print("Stopping engine")
        self.stop_event.set()
        self.api_thread.join(timeout=2)