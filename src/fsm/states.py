from enum import Enum

class States(Enum):
    """Possible states a driver for a team (or solo) might be in"""

    IDLE = 0
    ON_TRACK = 1
    ON_PIT_ROAD = 2
    IN_PIT_BOX = 3
    FINISHED = 4
    DISCONNECTED = 5
