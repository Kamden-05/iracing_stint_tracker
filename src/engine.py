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
        self.user_name = user_name
        self.api_url = api_base_url

        self._setup_api()
        self._setup_fsm_managers()
        self._setup_telemetry()

    def _setup_api(self):
        self.api_client = APIClient(self.api_url)
        self.api_worker = APIWorker(self.context, self.api_client, self.queue, self.stop_event)

        self.api_thread = threading.Thread(
            target=self.api_worker.run, daemon=True
        )
    def _setup_fsm_managers(self):
        self.fsm = DriverFSM()
        self.managers = [
            SessionManager(self.context, self.queue),
            StintManager(self.context, self.queue),
        ]
        self.fsm.attach_managers(self.managers)

    def _setup_telemetry(self):
        self.telemetry_loop = TelemetryLoop(
            ir_client=IRacingClient(),
            fsm=self.fsm,
            user_name=self.user_name,
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

    def reset(self):
        self.telemetry_loop.stop()
        self.telemetry_thread.join(timeout=2)

        self.context.reset()

        self._setup_fsm_managers()
        self._setup_telemetry()
        self.telemetry_thread.start()
