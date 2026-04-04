import time
import threading
import logging
from typing import TYPE_CHECKING, Optional, Any
from irsdk import SessionState, Flags

if TYPE_CHECKING:
    from src.fsm import DriverFSM
    from src.telemetry import IRacingClient

logger = logging.getLogger(__name__)


class TelemetryLoop:

    def __init__(
        self,
        ir_client: "IRacingClient",
        fsm: "DriverFSM",
        session_reset_event: threading.Event,
        delay_ticks: int,
        hz: int = 60,
    ):
        self.connected: bool = False
        self._stop_event = threading.Event()
        self.session_reset_event = session_reset_event

        self.ir: "IRacingClient" = ir_client
        self.fsm: "DriverFSM" = fsm
        self.interval: float = 1.0 / hz
        self.delay_ticks = delay_ticks
        self.final_lap_tick = None

        self.prev_user_in_car: bool = False
        self.prev_session_id: Optional[int] = None
        self.prev_on_pit_road: bool = False
        self.prev_in_pit_box: bool = False
        self.session_started: bool = False
        self.session_finished: bool = False
        self.final_lap_completed: Optional[int] = None

    def _get_tick_data(self) -> dict[str, Any]:
        data = {}

        for key in self.fsm.required_fields:
            try:
                data[key] = self.ir.get(key)
            except Exception:
                data[key] = None

        return data

    # TODO make sure race doesnt start under the pace car / before the green flag
    def _check_race_start(self) -> bool:
        session_info = self.ir.get("SessionInfo")
        sessions = session_info.get("Sessions", [])
        session_num = self.ir.get("SessionNum")

        session_type = sessions[session_num].get("SessionType", None)

        return (
            session_type == "Race"
            and self.ir.get("SessionState") == SessionState.racing
            and self.ir.get("PlayerCarClassPosition") > 0
        )

    def _check_race_end(self) -> bool:
        flags = self.ir.get("SessionFlags")
        session_num = self.ir.get("SessionNum")
        driver_in_car = self.ir.get("IsOnTrack")
        tow = self.ir.get("PlayerCarTowTime") > 0.0
        lap_completed = self.ir.get("LapCompleted")
        current_tick = self.ir.get("SessionTick")
        session_state = self.ir.get("SessionState")

        if session_num != 2:
            return False

        if session_state == SessionState.cool_down:
            return True

        off_track = not driver_in_car or tow
        if session_state == SessionState.checkered and off_track:
            return True

        is_checkered = flags & Flags.checkered

        if self.final_lap_completed is not None and not is_checkered:
            self.final_lap_completed = None
            self.final_lap_tick = None

        if is_checkered:
            if self.final_lap_completed is None:
                self.final_lap_completed = lap_completed
                return False

            finished_final_lap = lap_completed > self.final_lap_completed

            if finished_final_lap and self.final_lap_tick is None:
                self.final_lap_tick = current_tick

            ticks_since_final_lap = (
                current_tick - self.final_lap_tick if self.final_lap_tick else 0
            )

            return finished_final_lap and ticks_since_final_lap >= self.delay_ticks

        return False

    def _signal_session_change(self):
        self.session_reset_event.set()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():

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
                break

            self.prev_session_id = current_session_id

            on_track = bool(self.ir.get("IsOnTrackCar", False))
            on_pit_road = bool(self.ir.get("OnPitRoad", False))
            pit_active = bool(self.ir.get("PitstopActive", False))
            tow_time = float(self.ir.get("PlayerCarTowTime", 0.0))

            # FSM transitions

            user_is_driving = on_track or (tow_time > 0.0 and self.prev_user_in_car)

            tick_data = self._get_tick_data()

            # update manager state

            for m in self.fsm.managers:
                m.on_tick(tick_data, self.fsm.state, user_is_driving)

            if not self.session_finished:

                # session start
                if self._check_race_start() and not self.session_started:
                    self.session_started = True
                    self.fsm.session_start()
                    logger.debug("Session started")

                # session finish
                if self._check_race_end():
                    self.session_finished = True
                    self.fsm.session_finish()
                    logger.debug("Session finished")
                    continue

                if self.session_started:
                    if user_is_driving:
                        # enter pit road
                        if not self.prev_on_pit_road and (
                            on_pit_road or tow_time > 0.0
                        ):
                            logger.debug("Entered pit road")
                            self.fsm.enter_pit_road()

                        # exit pit road
                        if self.prev_on_pit_road and not on_pit_road:
                            logger.debug("Exited pit road")
                            self.fsm.exit_pit_road()

                        # enter pit box
                        if not self.prev_in_pit_box and pit_active:
                            logger.debug("Entered pit box")
                            self.fsm.enter_pit_box()

                        # exit pit box
                        if self.prev_in_pit_box and not pit_active:
                            logger.debug("Exited pit box")
                            self.fsm.exit_pit_box()

                    # driver swaps
                    if self.prev_user_in_car and not user_is_driving:
                        self.fsm.driver_swap_out()

                    if not self.prev_user_in_car and user_is_driving:
                        self.fsm.driver_swap_in()

            # update prev values
            self.prev_user_in_car = user_is_driving
            self.prev_on_pit_road = on_pit_road
            self.prev_in_pit_box = pit_active

            time.sleep(self.interval)
