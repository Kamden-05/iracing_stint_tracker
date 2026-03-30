from queue import Queue
import threading
import logging
from src.fsm import DriverFSM
from src.telemetry import IRacingClient, TelemetryLoop
from src.api import APIClient, APIWorker
from src.context import RaceContext
from src.managers import SessionManager, StintManager, LapManager, PitstopManager
from src.exporters import ExcelExporter

logger = logging.getLogger(__name__)


class AppEngine:
    def __init__(
        self,
        api_base_url: str,
        enable_excel: bool,
    ):
        self.context = RaceContext()
        self.queue = Queue()
        self.enable_excel = enable_excel
        self.stop_event = threading.Event()
        self.session_reset_event = threading.Event()
        self.api_url = api_base_url

        self._setup_api()
        self._setup_fsm_managers()
        self._setup_telemetry()

        self.session_reset_thread = threading.Thread(
            target=self._session_reset_watcher, daemon=True
        )

    def _setup_api(self):
        if self.api_url:
            self.api_client = APIClient(self.api_url)
            self.api_worker = APIWorker(
                self.context, self.api_client, self.queue, self.stop_event
            )
            self.api_thread = threading.Thread(target=self.api_worker.run, daemon=True)
        else:
            self.api_thread = None

    def _setup_fsm_managers(self):
        self.fsm = DriverFSM()
        excel = ExcelExporter() if self.enable_excel else None
        self.managers = [
            SessionManager(self.context, self.queue, excel),
            StintManager(self.context, self.queue, excel),
            PitstopManager(self.context, self.queue, excel),
            LapManager(self.context, self.queue, excel),
        ]
        self.fsm.attach_managers(self.managers)

    def _setup_telemetry(self):
        self.telemetry_loop = TelemetryLoop(
            ir_client=IRacingClient(),
            fsm=self.fsm,
            session_reset_event=self.session_reset_event,
        )

        self.telemetry_thread = threading.Thread(
            target=self.telemetry_loop.run, daemon=True
        )

    def _session_reset_watcher(self):
        while not self.stop_event.is_set():
            if self.session_reset_event.wait(timeout=1):
                self.session_reset_event.clear()
                self.reset()

    def start(self):
        if self.api_thread:
            logger.info("Starting API Worker")
            self.api_thread.start()
        else:
            logger.info("No API Thread")

        logger.info("Starting telemetry loop")
        self.telemetry_thread.start()

        logger.info("Starting session reset watcher")
        self.session_reset_thread.start()

    def stop(self):
        logger.info("Stopping engine")
        self.stop_event.set()
        if self.api_thread:
            self.api_thread.join()
        self.telemetry_loop.stop()
        self.telemetry_thread.join()

    def reset(self):
        logger.info("Resetting engine...")
        self.telemetry_loop.stop()
        self.telemetry_thread.join()

        self.context.reset()

        self._setup_fsm_managers()
        self._setup_telemetry()

        self.telemetry_thread.start()
