from enum import Enum, auto


class Status(Enum):
    CONNECTED = auto()
    RUNNING = auto()
    WAITING = auto()
    DISCONNECTED = auto()
    STARTUP = auto()


class Header(Enum):
    IRACING = "iRacing"
    API = "API"
    TRACKER = "Tracker"
