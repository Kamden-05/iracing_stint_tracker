import os
import logging
import sys
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication
from src.engine import AppEngine
from src.gui import StintTrackerWidget, GUINotifier


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
    handlers=[
        logging.FileHandler("stint_tracker.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


APP_NAME = "Stint Tracker"


def main():
    app = QApplication([])

    widget = StintTrackerWidget()
    widget.setWindowTitle(APP_NAME)

    load_dotenv()
    api_url = os.getenv("TEST_URL")

    engine = AppEngine(api_base_url=None, enable_excel=True)
    engine.start()

    notifier = GUINotifier(engine)
    engine.notifier = notifier
    notifier.status_data_ready.connect(widget.on_status_change)
    notifier.start()

    widget.show()

    def cleanup():
        engine.notifier = None
        notifier.stop()
        engine.stop()

    app.aboutToQuit.connect(cleanup)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
