from src.fsm.driver_fsm import States

class BaseManager:
    def handle_event(self, event: str, telem: dict[str, any], ctx: dict[str, any]):
        pass

    def on_tick(self, telem: dict[str, any], state: States):
        pass