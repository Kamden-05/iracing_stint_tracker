from enum import Enum
from typing import Optional
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
    [
        "finish_session",
        [States.ON_TRACK, States.ON_PIT_ROAD, States.IN_PIT_BOX, States.IDLE],
        States.FINISHED,
    ],
]

class DriverFSM(object):

    state: States
    set_state: callable

    def __init__(self):
        self.machine = Machine(
            model=self,
            states=States,
            transitions=TRANSITIONS,
            initial=States.DISCONNECTED,
        )

        self.last_state: Optional[States] = None


    def save_state(self):
        if self.state != States.DISCONNECTED:
            self.last_state = self.state
    
    def reconnect(self):
        if self.last_state:
            self.set_state(self.last_state)
        else:
            self.set_state(States.IDLE)