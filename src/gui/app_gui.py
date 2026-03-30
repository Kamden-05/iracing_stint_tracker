import sys
import logging
from src.gui.constants import Status, Header
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QGridLayout
from PySide6.QtGui import QFont, QIcon

APP_NAME = "Stint Tracker"

logger = logging.getLogger(__name__)


class StintTrackerWidget(QWidget):
    ICON_CHAR = "⬤"
    WINDOW_HEIGHT = 150
    WINDOW_WIDTH = 325
    FONT_SIZE = 12
    ICON_PATH = r"src\gui\resources\icon.ico"

    STATUS_MAPPING = {
        Status.CONNECTED: ("green", "Connected"),
        Status.DISCONNECTED: ("red", "Disconnected"),
        Status.WAITING: ("orange", "Waiting..."),
        Status.RUNNING: ("green", "Running"),
        Status.STARTUP: ("white", "Initializing..."),
    }

    def __init__(self):
        super().__init__()

        # Display details
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        font = QFont()
        font.setPointSize(self.FONT_SIZE)
        self.setFont(font)
        self.setWindowIcon(QIcon(self.ICON_PATH))

        # Layout details
        layout = QGridLayout()
        layout.setContentsMargins(30, 0, 0, 0)

        self.status_labels = {}

        for row, header in enumerate(Header):

            color, status_text = self.STATUS_MAPPING[Status.STARTUP]

            title_label = QLabel(header.value)
            status_label = QLabel(self._build_status_text(color, status_text))

            layout.addWidget(title_label, row, 0)
            layout.addWidget(status_label, row, 1)

            self.status_labels[header] = status_label

        self.setLayout(layout)

    def _build_status_text(self, color: str, text: str) -> str:
        icon = f'<span style="color:{color};">{self.ICON_CHAR}</span>'
        return f"{icon} {text}"

    def _set_status(self, header: Header, color: str, text: str):
        status = self._build_status_text(color, text)
        self.status_labels[header].setText(status)

    def on_status_change(self, header: Header, status: Status):
        if not status in self.STATUS_MAPPING:
            logger.warning("Invalid status %s for header %s", status, header)

        color, text = self.STATUS_MAPPING.get(status, ("gray", "Unkown"))
        self._set_status(header, color, text)


if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationName(APP_NAME)
    widget = StintTrackerWidget()
    widget.setWindowTitle(APP_NAME)
    widget.show()
    sys.exit(app.exec())
