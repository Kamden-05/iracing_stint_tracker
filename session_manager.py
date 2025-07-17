from iracing_interface import IracingInterface

# TODO: could we potentially want to track stints for other drivers?
# what data from other drivers would be available that would be useful?


class SessionManager:
    session_type: str = None

    def __init__(self, ir_interface: IracingInterface):
        self.ir = ir_interface
        self.stints = []
        self.current_stint = None
        self.last_pitstop_active = False
        self.last_recorded_lap = -1

    # check irsdk connection

    def connected(self) -> bool:
        return self.ir.check_connection()

    # handle different session types

    def get_session_type() -> str:
        pass
