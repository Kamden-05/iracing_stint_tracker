from typing import Optional
from transitions import Machine, EventData
from src.fsm.states import States
from src.managers.base_manager import BaseManager


TRANSITIONS = [
    # [event, source, destination]
    # connection/initialization
    ["connect", States.DISCONNECTED, States.IDLE],
    ["disconnect", "*", States.DISCONNECTED],
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
    last_telem: dict[str, any]

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

    def reconnect(self):
        if self.last_state:
            self.set_state(self.last_state)
        else:
            self.set_state(States.IDLE)

    def attach_managers(self, managers: list[BaseManager]):
        self.managers = managers
        self.required_fields = set()

        for m in self.managers:
            self.required_fields.update(m.required_fields.keys())

    def _broadcast(self, event_name: str, event: EventData):
        ctx = {
            "source": event.transition.source,
            "dest": event.transition.dest,
            "event": event.event.name,
        }

        for m in self.managers:
            m.handle_event(event_name, self.last_telem, ctx)

    # state based callbacks

    def on_enter_ON_PIT_ROAD(self, event: EventData):
        self._broadcast("enter_pit_road", event)

    def on_exit_ON_PIT_ROAD(self, event: EventData):
        self._broadcast("exit_pit_road", event)

    def on_enter_IN_PIT_BOX(self, event: EventData):
        self._broadcast("enter_pit_box", event)

    def on_exit_IN_PIT_BOX(self, event: EventData):
        self._broadcast("exit_pit_box", event)

    def on_enter_FINISHED(self, event: EventData):
        self._broadcast("finished", event)

    def on_enter_DISCONNECTED(self, event: EventData):
        self._broadcast("disconnected", event)

    # event based callbacks

    def _on_session_start(self, event: EventData):
        self._broadcast("session_start", event)

    def _on_driver_swap_in(self, event: EventData):
        self._broadcast("driver_swap_in", event)

    def _on_driver_swap_out(self, event: EventData):
        self._broadcast("driver_swap_out", event)
