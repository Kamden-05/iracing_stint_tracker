from iracing_interface import IracingInterface
from stint import Stint

# TODO: could we potentially want to track stints for other drivers?
# what data from other drivers would be available that would be useful?


class SessionManager:

    def __init__(self, ir_interface: IracingInterface):
        self.ir = ir_interface
        self.stints = []
        self.current_stint = None
        self.last_pitstop_active = False
        self.last_recorded_lap = -1

    # handle different session types

    def update_prev_refuel(self, prev_stint: Stint) -> Stint:
        prev_stint["Refuel Qty."] = max(
            0,
            round(
                self.current_stint.start_fuel - prev_stint["End Fuel Qty."],
                2,
            ),
        )

        return prev_stint

    def record_stint(self) -> dict:
        end_time = self.ir.get_session_time()
        end_fuel = self.ir.get_fuel_level()
        end_pos = self.ir.get_player_position()
        incidents = self.ir.get_team_incidents()
        service_time = self.ir.get_service_time()
        tire_replacement = self.ir.get_tire_replacement()
        end_fast_repairs = self.ir.get_fast_repairs()

        stint_data = self.current_stint.to_dict(
            end_time,
            end_fuel,
            end_pos,
            incidents,
            service_time,
            tire_replacement,
            end_fast_repairs,
        )

        return stint_data

    def process_race(self):
        current_lap = self.ir.get_lap()
        pitstop_active = self.ir.get_pitstop_active()

        if self.current_stint is None and not pitstop_active:
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
                self.stints[-1] = self.update_prev_refuel(self.stints[-1])

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
            self.stints.append(self.record_stint())
            self.current_stint = None
            print("Stint recorded")

        self.last_pitstop_active = pitstop_active

    def export_stints(self) -> list[dict]:
        return self.stints
