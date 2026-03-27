from typing import Optional
from transitions import Machine
from src.fsm.states import States
from src.managers.base_manager import BaseManager


TRANSITIONS = [
    # [event, source, destination, conditions, unless, after]
    # connection/initialization
    ["connect", States.DISCONNECTED, States.IDLE, None, None, None],
    ["disconnect", "*", States.DISCONNECTED, None, None, None],
    # pre-session / idle
    ["session_start", States.IDLE, States.ON_TRACK, None, None, "_on_session_start"],
    [
        "driver_swap_out",
        States.IN_PIT_BOX,
        States.IDLE,
        None,
        None,
        "_on_driver_swap_out",
    ],
    [
        "driver_swap_in",
        States.IDLE,
        States.IN_PIT_BOX,
        None,
        None,
        "_on_driver_swap_in",
    ],
    # on track
    [
        "enter_pit_road",
        States.ON_TRACK,
        States.ON_PIT_ROAD,
        None,
        None,
        "_on_enter_pit_road",
    ],
    [
        "exit_pit_road",
        States.ON_PIT_ROAD,
        States.ON_TRACK,
        None,
        None,
        "_on_exit_pit_road",
    ],
    # pit stop
    [
        "enter_pit_box",
        States.ON_PIT_ROAD,
        States.IN_PIT_BOX,
        None,
        None,
        "_on_enter_pit_box",
    ],
    [
        "exit_pit_box",
        States.IN_PIT_BOX,
        States.ON_PIT_ROAD,
        None,
        None,
        "_on_exit_pit_box",
    ],
    # post-session
    [
        "finish_session",
        [States.ON_TRACK, States.ON_PIT_ROAD, States.IN_PIT_BOX, States.IDLE],
        States.FINISHED,
        None,
        None,
        "_on_session_finish",
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

    def connect(self):
        if self.last_state:
            self.machine.set_state(self.last_state)
        else:
            self.set_state(States.IDLE)

    def attach_managers(self, managers: list[BaseManager]):
        self.managers = managers
        self.required_fields = set()

        for m in self.managers:
            self.required_fields.update(m.required_fields.keys())

    def _broadcast(self, event_name: str):
        for m in self.managers:
            m.handle_event(event_name)

    def _on_session_start(self):
        self._broadcast("session_start")

    def _on_session_finish(self):
        self._broadcast("session_finish")

    def _on_enter_pit_road(self):
        self._broadcast("enter_pit_road")

    def _on_exit_pit_road(self):
        self._broadcast("exit_pit_road")

    def _on_enter_pit_box(self):
        self._broadcast("enter_pit_box")

    def _on_exit_pit_box(self):
        self._broadcast("exit_pit_box")

    def _on_driver_swap_in(self):
        self._broadcast("driver_swap_in")

    def _on_driver_swap_out(self):
        self._broadcast("driver_swap_out")
