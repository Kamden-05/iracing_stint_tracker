from typing import Optional
import logging
from transitions import Machine, EventData
from src.fsm.states import States
from src.managers.base_manager import BaseManager

logger = logging.getLogger(__name__)

TRANSITIONS = [
    # [event name, source, destination, conditions, unless, after]
    # connection/initialization
    ["connect", States.DISCONNECTED, States.IDLE, None, None, None],
    ["disconnect", "*", States.DISCONNECTED, None, None, None],
    # pre-session / idle
    ["session_start", States.IDLE, States.ON_TRACK, None, None, "_handle_event"],
    [
        "driver_swap_out",
        States.IN_PIT_BOX,
        States.IDLE,
        None,
        None,
        "_handle_event",
    ],
    [
        "driver_swap_in",
        States.IDLE,
        States.IN_PIT_BOX,
        None,
        None,
        "_handle_event",
    ],
    # on track
    [
        "enter_pit_road",
        States.ON_TRACK,
        States.ON_PIT_ROAD,
        None,
        None,
        "_handle_event",
    ],
    [
        "exit_pit_road",
        States.ON_PIT_ROAD,
        States.ON_TRACK,
        None,
        None,
        "_handle_event",
    ],
    # pit stop
    [
        "enter_pit_box",
        States.ON_PIT_ROAD,
        States.IN_PIT_BOX,
        None,
        None,
        "_handle_event",
    ],
    [
        "exit_pit_box",
        States.IN_PIT_BOX,
        States.ON_PIT_ROAD,
        None,
        None,
        "_handle_event",
    ],
    # post-session
    [
        "session_finish",
        [States.ON_TRACK, States.ON_PIT_ROAD, States.IN_PIT_BOX, States.IDLE],
        States.FINISHED,
        None,
        None,
        "_handle_event",
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
            send_event=True,
        )

        self.last_state: Optional[States] = None
        self.managers: list[BaseManager] = []
        self.required_fields: set[str] = set()

    def save_state(self):
        if self.state != States.DISCONNECTED:
            self.last_state = self.state

    def restore_state(self):
        if self.last_state:
            self.machine.set_state(self.last_state)
        else:
            self.state = States.IDLE

    def attach_managers(self, managers: list[BaseManager]):
        self.managers = managers
        self.required_fields = set()

        for m in self.managers:
            self.required_fields.update(m.required_fields.keys())

    def _handle_event(self, event_data: EventData):
        logger.debug(f"Event: {event_data.event.name}")
        logger.debug(f"From: {event_data.transition.source}")
        logger.debug(f"To: {event_data.transition.dest}")
        logger.debug(f"Current state: {event_data.state}")
        self._broadcast(event_data.event.name)

    def _broadcast(self, event_name: str):
        for m in self.managers:
            m.handle_event(event_name)
