import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.fsm.driver_fsm import DriverFSM
    from src.telemetry.iracing_client import IRacingClient


class TelemetryLoop:
    def __init__(
        self, ir_client: "IRacingClient", fsm: "DriverFSM", user_name: str, hz: int = 60
    ):
        self.connected: bool = False

        self.user_name: str = user_name
        self.ir: "IRacingClient" = ir_client
        self.fsm: "DriverFSM" = fsm
        self.interval: float = 1.0 / hz

        self.prev_on_track: bool = False
        self.prev_on_pit_road: bool = False
        self.prev_in_pit_box: bool = False
        self.prev_session_state: Optional[int] = None
        self.prev_driver_name: Optional[str] = None

    def _get_current_driver_name(self) -> Optional[str]:
        try:
            car_id = int(self.ir.get("PlayerCarIdx"))
            drivers = self.ir.get("DriverInfo")["Drivers"]

            return drivers[car_id]["UserName"]
        except Exception:
            return None

    def run(self):
        while True:

            # connection handling

            if not self.connected:
                if self.ir.connect():
                    self.connected = True
                    self.fsm.connect()
                else:
                    time.sleep(self.interval)
                    continue

            if not self.ir.is_connected:
                self.connected = False
                self.fsm.disconnect()
                # TODO: self.manager.handle_disconnect
                time.sleep(self.interval)
                continue

            # telemetry reading

            self.ir.update()

            on_track = bool(self.ir.get("IsOnTrack", False))
            on_pit_road = bool(self.ir.get("OnPitRoad", False))
            pit_active = bool(self.ir.get("PitstopActive", False))
            tow_time = float(self.ir.get("PlayerCarTowTime", 0.0))
            session_state = self.ir.get("SessionState")
            driver_name = self._get_current_driver_name()

            # FSM transitions

            # session start
            if session_state == 3 and self.prev_session_state != 3:
                self.fsm.session_start()

            # enter pit road
            if not self.prev_on_pit_road and (on_pit_road or tow_time > 0.0):
                self.fsm.enter_pit_road()

            # exit pit road
            if self.prev_on_pit_road and not on_pit_road:
                self.fsm.exit_pit_road()

            # enter pit box
            if not self.prev_in_pit_box and pit_active:
                self.fsm.enter_pit_box()

            # exit pit box
            if self.prev_in_pit_box and not pit_active:
                self.fsm.exit_pit_box()

            # driver swaps
            if driver_name != self.prev_driver_name:

                # user enters car
                if driver_name == self.user_name:
                    self.fsm.driver_swap_in()
                
                # user exits car
                elif self.prev_driver_name == self.user_name:
                    self.fsm.driver_swap_out()

            # session finish
            if session_state == 5 and self.prev_session_state != 5:
                self.fsm.finish_session()

            # TODO: update mnager values, need to write manager classes first

            # update prev values
            self.prev_on_track = on_track
            self.prev_on_pit_road = on_pit_road
            self.prev_in_pit_box = pit_active
            self.prev_session_state = session_state
            self.prev_driver_name = driver_name

            time.sleep(self.interval)
