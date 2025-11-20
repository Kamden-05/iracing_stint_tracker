from queue import Queue
from typing import Any
from src.fsm.driver_fsm import States
from src.context.session_context import SessionContext

class BaseManager:
    required_fields: set[str] = set()

    def __init__(self, context: SessionContext, queue: Queue):
        self.context = context
        self.queue = queue

    def handle_event(self, event: str, telem: dict[str, Any], ctx: dict[str, Any]):
        pass

    def on_tick(self, telem: dict[str, Any], state: States):
        pass