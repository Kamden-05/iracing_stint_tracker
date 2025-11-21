import time
from typing import TYPE_CHECKING, Optional, Any
from irsdk import SessionState, Flags

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
        self.session_started: bool = False
        self.session_finished: bool = False
        self.final_lap_completed: Optional[bool] = None
        self.prev_driver_name: Optional[str] = user_name

    def _get_current_driver_name(self) -> Optional[str]:
        try:
            car_id = int(self.ir.get("PlayerCarIdx"))
            drivers = self.ir.get("DriverInfo")["Drivers"]

            return drivers[car_id]["UserName"]
        except Exception:
            return None

    def _get_tick_data(self) -> dict[str, Any]:
        data = {}
        get = self.ir.get

        for key in self.fsm.required_fields:
            try:
                data[key] = get(key)
            except Exception:
                data[key] = None

        return data

    def _check_race_start(self) -> bool:
        return (
            self.ir.get("SessionState") == SessionState.racing
            and self.ir.get("PlayerCarClassPosition") > 0
        )
    
    def _check_race_end(self) -> bool:
        flags = self.ir.get("SessionFlags")
        on_track = self.ir.get("IsOnTrack")
        tow = self.ir.get("PlayerCarTowTime") > 0.0
        lap_completed = self.ir.get("LapCompleted")

        if flags & Flags.checkered:
            if self.final_lap_completed is None:
                self.final_lap_completed = lap_completed
                return False

            # Has the driver finished their final lap yet?
            finished_final_lap = lap_completed > self.final_lap_completed
            off_track = not on_track or tow

            return finished_final_lap or off_track

        return False

    def run(self):
        while not self.session_finished:

            # connection handling

            if not self.connected:
                if self.ir.connect():
                    self.connected = True
                    if self.fsm.last_state:
                        self.fsm.reconnect()
                    else:
                        self.fsm.connect()
                else:
                    time.sleep(self.interval)
                    continue

            if not self.ir.is_connected:
                self.connected = False
                self.fsm.save_state()
                self.fsm.disconnect()
                time.sleep(self.interval)
                continue

            # telemetry reading

            self.ir.update()

            on_track = bool(self.ir.get("IsOnTrack", False))
            on_pit_road = bool(self.ir.get("OnPitRoad", False))
            pit_active = bool(self.ir.get("PitstopActive", False))
            tow_time = float(self.ir.get("PlayerCarTowTime", 0.0))
            driver_name = self._get_current_driver_name()

            tick_data = self._get_tick_data()

            self.fsm.last_telem = tick_data

            # FSM transitions

            # session start
            if self._check_race_start() and not self.session_started:
                self.session_started = True
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
            if self._check_race_end() and not self.session_finished:
                self.session_finished = True
                self.fsm.finish_session()

            # update managers
            for m in self.fsm.managers:
                m.on_tick(tick_data, self.fsm.state)

            # update prev values
            self.prev_on_track = on_track
            self.prev_on_pit_road = on_pit_road
            self.prev_in_pit_box = pit_active
            self.prev_driver_name = driver_name

            time.sleep(self.interval)
