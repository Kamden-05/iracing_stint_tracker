from iracing_interface import IracingInterface
from stint import Stint
from typing import List

# TODO: could we potentially want to track stints for other drivers?
# what data from other drivers would be available that would be useful?


class SessionManager:

    def __init__(self, ir_interface: IracingInterface):
        self.ir = ir_interface
        self.stints: List[Stint] = []
        self.current_stint: Stint = None
        self.last_pitstop_active = False
        self.last_recorded_lap = -1
        self.prev_completed = 0
        self.pit_start_time = 0
        self.pit_end_time = 0

    # handle different session types

    def record_stint(self):
        self.current_stint.end_time = self.ir.get_session_time()
        self.current_stint.end_position = self.ir.get_player_position()
        self.current_stint.end_fuel = self.ir.get_fuel_level()
        self.current_stint.incidents = self.ir.get_team_incidents()
        self.current_stint.required_repair_time = self.ir.get_repair_time()
        self.current_stint.optional_repair_time = self.ir.get_optional_repair_time()
        self.current_stint.tire_replacement = self.ir.get_tire_replacement()
        self.current_stint.end_fast_repairs = self.ir.get_fast_repairs()
        self.current_stint.laps_completed = (
            self.ir.get_completed_laps() - self.prev_completed
        )

    def update_prev_refuel(self):
        self.stints[-1].refuel_amount = max(
            0, self.current_stint.start_fuel - self.stints[-1].end_fuel
        )

    def update_prev_service_time(self):
        self.stints[-1].service_time = self.pit_end_time - self.pit_start_time

    # TODO: fix logic to update service time if not all optional repairs are taken
    def process_race(self):
        current_lap = self.ir.get_lap()
        pitstop_active = self.ir.get_pitstop_active()

        if not pitstop_active:
            if self.last_pitstop_active:
                self.pit_end_time = self.ir.get_session_time()
                self.update_prev_service_time()

            if self.current_stint is None:
                self.current_stint = Stint(
                    driver=self.ir.get_driver_name(),
                    start_time=self.ir.get_session_time(),
                    laps=[],
                    start_position=self.ir.get_player_position(),
                    start_incidents=self.ir.get_team_incidents(),
                    start_fuel=self.ir.get_fuel_level(),
                    start_fast_repairs=self.ir.get_fast_repairs(),
                )

                if len(self.stints) > 0:
                    self.update_prev_refuel()
                print("new stint started")

        if (
            self.current_stint
            and current_lap > 1
            and current_lap > self.last_recorded_lap
        ):
            lap_time = self.ir.get_last_lap_time()
            self.current_stint.laps.append(lap_time)
            self.last_recorded_lap = current_lap

        if (
            pitstop_active
            and not self.last_pitstop_active
            and self.current_stint is not None
        ):
            # Pit started, record stint
            self.pit_start_time = self.ir.get_session_time()
            self.record_stint()
            self.stints.append(self.current_stint)
            self.current_stint = None
            self.prev_completed = self.ir.get_completed_laps()
            print("Stint recorded")

        self.last_pitstop_active = pitstop_active

    # TODO: change as list of dicts for return instead of list of Stints
    def export_stint_data(self) -> list[dict]:
        return [stint.to_dict() for stint in self.stints]
