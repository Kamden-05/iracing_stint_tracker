from queue import Queue
from typing import Any
from src.fsm.driver_fsm import States
from src.context.race_context import RaceContext


class BaseManager:
    required_fields: dict[str, str] = {}

    def __init__(self, context: RaceContext, queue: Queue):
        self.context = context
        self.queue = queue

        for attr in self.required_fields.values():
            setattr(self, attr, None)

    def handle_event(self, event: str, telem: dict[str, Any], ctx: dict[str, Any]):
        pass

    def on_tick(self, telem: dict[str, Any], state: States):
        for telem_key, attr_name in self.required_fields.items():
            setattr(self, attr_name, telem[telem_key])
