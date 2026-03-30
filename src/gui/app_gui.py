import sys
from enum import Enum
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QGridLayout
from PySide6.QtGui import QFont, QIcon

APP_NAME = "Stint Tracker"


class StatusColor(Enum):
    GREEN = "green"
    ORANGE = "orange"
    RED = "red"


class StintTrackerWidget(QWidget):
    ICON_CHAR = "⬤"
    GOOD_COLOR = "green"
    BAD_COLOR = "red"
    WAITING_COLOR = "orange"
    WINDOW_HEIGHT = 150
    WINDOW_WIDTH = 325
    FONT_SIZE = 12
    ICON_PATH = r"src\gui\resources\icon.ico"

    def __init__(self):
        super().__init__()

        # Display details
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        font = QFont()
        font.setPointSize(self.FONT_SIZE)
        self.setFont(font)
        self.setWindowIcon(QIcon(self.ICON_PATH))

        # Layout details
        self.ir_label = QLabel(
            f"{self._get_status_icon(StatusColor.GREEN)} Connected"
        )
        self.api_label = QLabel(
            f"{self._get_status_icon(StatusColor.RED)} Disconnected"
        )
        self.tracker_label = QLabel(
            f"{self._get_status_icon(StatusColor.ORANGE)} Waiting"
        )

        layout = QGridLayout()

        layout.setContentsMargins(30, 0, 0, 0)
        layout.addWidget(QLabel("iRacing"), 0, 0)
        layout.addWidget(self.ir_label, 0, 1)

        layout.addWidget(QLabel("API"), 1, 0)
        layout.addWidget(self.api_label, 1, 1)

        layout.addWidget(QLabel("Tracker"), 2, 0)
        layout.addWidget(self.tracker_label, 2, 1)

        self.setLayout(layout)

    def _get_status_icon(self, color: StatusColor):
        return f'<span style="color:{color.value};">{self.ICON_CHAR}</span>'

    def set_ir_status(self):
        pass

    def set_api_status(self):
        pass

    def set_tracker_status(self):
        pass


if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationName(APP_NAME)
    widget = StintTrackerWidget()
    widget.setWindowTitle(APP_NAME)
    widget.show()
    sys.exit(app.exec())
