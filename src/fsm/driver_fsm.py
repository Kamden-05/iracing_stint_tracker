from enum import Enum
from transitions import Machine

class States(Enum):
    """Possible states a driver for a team (or solo) might be in"""
    IDLE = 0
    ON_TRACK = 1
    ON_PIT_ROAD = 2
    IN_PIT_BOX = 3
    FINISHED = 4
    DISCONNECTED = 5

TRANSITIONS = [
    # [event, source, destination]
    # connection/initialization
    ["connect", States.DISCONNECTED, States.IDLE],
    ["disconnect", "*", States.DISCONNECTED],
    
    # pre-session / idle
    ["session_start", States.IDLE, States.ON_TRACK],
    ["driver_swap_out", States.IN_PIT_BOX, States.IDLE],
    ["driver_swap_in", States.IDLE, States.IN_PIT_BOX],

    # on track
    ["enter_pit_road", States.ON_TRACK, States.ON_PIT_ROAD],
    ["exit_pit_road", States.ON_PIT_ROAD, States.ON_TRACK],

    # pit stop
    ["enter_pit_box", States.ON_PIT_ROAD, States.IN_PIT_BOX],
    ["exit_pit_box", States.IN_PIT_BOX, States.ON_PIT_ROAD],

    # post-session
    ["finish_session", [States.ON_TRACK, States.ON_PIT_ROAD, States.IN_PIT_BOX, States.IDLE], States.FINISHED]
]

class DriverMachine(object):

    def __init__(self):
        self.machine = Machine(model=self, states=States, transitions=TRANSITIONS, initial=States.DISCONNECTED)
    