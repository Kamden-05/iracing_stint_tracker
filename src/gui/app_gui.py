import logging
from src.gui.constants import Status, Header
from PySide6.QtCore import Slot
from PySide6.QtCore import QObject, Signal, QTimer, QPoint
from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QGridLayout,
    QSystemTrayIcon,
    QMenu,
    QApplication,
)
from PySide6.QtGui import QFont, QIcon, QCloseEvent, QCursor

APP_NAME = "Stint Tracker"

logger = logging.getLogger(__name__)


class GUINotifier(QObject):
    status_data_ready = Signal(Header, Status)

    def __init__(self, engine, poll_rate_ms: int = 100):
        super().__init__()
        self.engine = engine
        self.timer = QTimer()
        self.timer.setInterval(poll_rate_ms)
        self.timer.timeout.connect(self.poll_engine)

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.stop()

    def poll_engine(self):
        if self.engine:
            self.engine.emit_gui_updates()


class StintTrackerWidget(QWidget):
    ICON_CHAR = "⬤"
    WINDOW_HEIGHT = 150
    WINDOW_WIDTH = 350
    FONT_SIZE = 12
    ICON_PATH = r"src\gui\resources\icon.ico"

    STATUS_MAPPING = {
        Status.CONNECTED: ("green", "Connected"),
        Status.DISCONNECTED: ("red", "Disconnected"),
        Status.WAITING: ("orange", "Waiting for race..."),
        Status.RUNNING: ("green", "Running"),
        Status.FINISHED: ("purple", "Session finished"),
        Status.STARTUP: ("white", "Initializing..."),
    }

    def __init__(self):
        super().__init__()

        # Display details
        self._quit_requested = False
        self.icon = QIcon(self.ICON_PATH)
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        font = QFont()
        font.setPointSize(self.FONT_SIZE)
        self.setFont(font)
        self.setWindowIcon(self.icon)

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

        self.tray = QSystemTrayIcon(self.icon)
        tray_menu = QMenu()

        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self._on_show_clicked)

        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self._on_quit_clicked)

        self.tray.activated.connect(self._on_tray_activated)

        self.tray.setContextMenu(tray_menu)
        self.tray.setToolTip(APP_NAME)
        self.tray.show()

    def _build_status_text(self, color: str, text: str) -> str:
        icon = f'<span style="color:{color};">{self.ICON_CHAR}</span>'
        return f"{icon} {text}"

    def _set_status(self, header: Header, color: str, text: str):
        status = self._build_status_text(color, text)
        self.status_labels[header].setText(status)

    def _on_show_clicked(self):
        self.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.Trigger:
            tray_geometry = self.tray.geometry()

            if tray_geometry.isValid():
                pos = QPoint(
                    tray_geometry.left(),
                    tray_geometry.top() - self.tray.contextMenu().sizeHint().height(),
                )
            else:
                pos = QCursor.pos()

            self.tray.contextMenu().popup(pos)

    def _on_quit_clicked(self):
        self._quit_requested = True
        QApplication.instance().quit()

    def closeEvent(self, event: QCloseEvent):
        if self._quit_requested:
            event.accept()
        else:
            event.ignore()  # ignore the default close
            self.hide()
            self.tray.showMessage(
                "Stint Tracker",
                "App minimized to tray",
                QSystemTrayIcon.Information,
                2000,
            )

    @Slot(Header, Status)
    def on_status_change(self, header: Header, status: Status):
        if not status in self.STATUS_MAPPING:
            logger.warning("Invalid status %s for header %s", status, header)

        color, text = self.STATUS_MAPPING.get(status, ("gray", "Unkown"))
        self._set_status(header, color, text)
