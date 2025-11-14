from enum import Enum
from transitions import Machine

class States(Enum):
    IDLE = 0
    ON_TRACK = 1
    ON_PIT_ROAD = 2
    IN_PIT_BOX = 3
    FINISHED = 4
    DISCONNECTED = 5


class RaceMachine(object):

    states = ['']