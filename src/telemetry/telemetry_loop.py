import time
import threading
from typing import TYPE_CHECKING, Optional, Any
from irsdk import SessionState, Flags

if TYPE_CHECKING:
    from src.fsm import DriverFSM
    from src.telemetry import IRacingClient


class TelemetryLoop:
    def __init__(
        self,
        ir_client: "IRacingClient",
        fsm: "DriverFSM",
        session_reset_event: threading.Event,
        hz: int = 60,
    ):
        self.connected: bool = False
        self._stop_event = threading.Event()
        self.session_reset_event = session_reset_event

        self.ir: "IRacingClient" = ir_client
        self.fsm: "DriverFSM" = fsm
        self.interval: float = 1.0 / hz

        self.prev_user_in_car: bool = False
        self.prev_session_id: Optional[int] = None
        self.prev_on_track: bool = False
        self.prev_on_pit_road: bool = False
        self.prev_in_pit_box: bool = False
        self.session_started: bool = False
        self.session_finished: bool = False
        self.final_lap_completed: Optional[bool] = None

    def _get_tick_data(self) -> dict[str, Any]:
        data = {}

        for key in self.fsm.required_fields:
            try:
                data[key] = self.ir.get(key)
            except Exception:
                data[key] = None

        return data

    def _check_race_start(self) -> bool:
        return (
            self.ir.get("SessionNum") == 2  # 0 for practice, 1 for quali, 2 for race
            and self.ir.get("SessionState") == SessionState.racing
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

    def _signal_session_change(self):
        self.session_reset_event.set()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set() and not self.session_finished:

            # connection handling

            if not self.connected:
                if self.ir.connect():
                    self.connected = True
                    self.fsm.restore_state()
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

            current_session_id = self.ir.get("WeekendInfo")["SubSessionID"]
            if (
                self.prev_session_id is not None
                and current_session_id != self.prev_session_id
            ):
                self._signal_session_change()
            self.prev_session_id = current_session_id

            on_track = bool(self.ir.get("IsOnTrackCar", False))
            on_pit_road = bool(self.ir.get("OnPitRoad", False))
            pit_active = bool(self.ir.get("PitstopActive", False))
            tow_time = float(self.ir.get("PlayerCarTowTime", 0.0))

            tick_data = self._get_tick_data()

            # FSM transitions

            user_is_driving = on_track or (tow_time > 0.0 and self.prev_user_in_car)

            # session start
            if self._check_race_start() and not self.session_started:
                self.session_started = True
                self.fsm.session_start()

            if self.session_started:
                if user_is_driving:
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
                if self.prev_user_in_car and not user_is_driving:
                    self.fsm.driver_swap_out()

                if not self.prev_user_in_car and user_is_driving:
                    self.fsm.driver_swap_in()

            # session finish
            if self._check_race_end() and not self.session_finished:
                self.session_finished = True
                self.fsm.finish_session()

            # update managers
            for m in self.fsm.managers:
                m.on_tick(tick_data)

            # update prev values
            self.prev_user_in_car = user_is_driving
            self.prev_on_track = on_track
            self.prev_on_pit_road = on_pit_road
            self.prev_in_pit_box = pit_active

            time.sleep(self.interval)
