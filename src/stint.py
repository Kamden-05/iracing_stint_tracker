from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from src.utils import format_time


@dataclass
class Stint:
    """Stint Start Values:"""

    # TODO: add a final_stint flag to indicate whether or not this is the last stint in the race
    stint_id: int
    driver: str
    start_time: float
    start_position: int
    start_incidents: int
    start_fuel: float
    start_fast_repairs: int
    laps: List[float] = field(default_factory=list)
    """Stint End Values:"""
    stint_length: Optional[float] = -1.0
    incidents: int = field(init=False)
    in_lap: Optional[float] = "N/A"
    out_lap: Optional[float] = -1.0
    avg_lap: Optional[float] = -1.0
    laps_completed: Optional[int] = -1
    end_position: Optional[int] = -1
    end_fast_repairs: int = field(init=False)

    def __post_init__(self):
        self.incidents = self.start_incidents
        self.end_fast_repairs = self.start_fast_repairs

    """Pit Values:"""
    end_fuel: Optional[float] = -1.0
    refuel_amount: Optional[float] = "N/A"
    required_repair_time: Optional[float] = -1.0
    optional_repair_time: Optional[float] = -1.0
    pit_service_duration: Optional[float] = 0.0
    pit_service_start_time: Optional[float] = 0.0
    tire_change: Optional[bool] = "N/A"
    repairs: Optional[bool] = "N/A"

    # TODO: handle final stint logic for pit_service_duration and in_lap
    def end_stint(
        self,
        session_time: float,
        position: float,
        incidents: int,
        fast_repairs: int,
        end_fuel: float,
        final: bool,
    ) -> None:
        self.stint_length = session_time - self.start_time
        self.end_position = position
        self.incidents = incidents - self.start_incidents
        self.end_fast_repairs = fast_repairs

        if final:
            self.end_fuel = end_fuel
        else:
            self.in_lap = self.laps[-1] if self.laps else 0.0
            self.repairs = self._check_repairs()
            self.pit_service_duration = session_time - self.pit_service_start_time

        self.out_lap = self.laps[0] if self.laps else 0.0

        self.avg_lap = (
            float(sum(self.laps)) / float(len(self.laps)) if self.laps else 0.0
        )
        self.laps_completed = len(self.laps)

        self.display()

    def record_pit(
        self,
        required_repair_time: float,
        optional_repair_time: float,
        end_fuel: float,
        reufel_amount: float,
        tires: bool,
        session_time: float,
    ) -> None:
        self.required_repair_time = required_repair_time
        self.optional_repair_time = optional_repair_time
        self.end_fuel = end_fuel
        self.refuel_amount = reufel_amount
        self.tire_change = tires
        self.pit_service_start_time = session_time

    def _check_repairs(self) -> bool:
        if (
            self.required_repair_time + self.optional_repair_time > 0
        ) or self.end_fast_repairs - self.start_fast_repairs > 0:
            return True
        else:
            return False

    def record_lap(self, lap_time) -> None:
        self.laps.append(lap_time)

    def display(self):
        """Print all values in the stint for easy review."""
        print(f"{' '*17}Stint {self.stint_id}")
        print(f"{'='*40}")
        print(f"Driver: {self.driver}")
        print(f"Start Time: {self.start_time}")
        print(f"Start Position: {self.start_position}")
        print(f"Start Incidents: {self.start_incidents}")
        print(f"Start Fuel: {self.start_fuel}")
        print(f"Start Fast Repairs: {self.start_fast_repairs}")
        print(f"Laps: {self.laps}")
        print(f"{'-'*40}")
        print(f"Stint Length: {format_time(self.stint_length)}")
        print(f"End Position: {self.end_position}")
        print(f"Incidents in Stint: {self.incidents}")
        print(f"Out Lap: {format_time(self.out_lap)}")
        print(
            f"In Lap: {format_time(self.in_lap) if isinstance(self.in_lap, float) else self.in_lap}"
        )
        print(f"Average Lap: {format_time(self.avg_lap)}")
        print(f"Laps Completed: {self.laps_completed}")
        print(f"{'-'*40}")
        print(f"End Fuel: {self.end_fuel}")
        print(f"Refuel Amount: {self.refuel_amount}")
        print(
            f"Required Repair Time: {format_time(self.required_repair_time) if self.required_repair_time > 0.0 else 'N/A'}"
        )
        print(
            f"Optional Repair Time: {format_time(self.optional_repair_time) if self.optional_repair_time > 0.0 else 'N/A'}"
        )
        print(
            f"Service Start Time: {format_time(self.pit_service_start_time) if self.pit_service_start_time > 0.0 else 'N/A'}"
        )
        print(
            f"Service Time: {format_time(self.pit_service_duration) if self.pit_service_duration > 0.0 else 'N/A'}"
        )
        print(f"Tire Change: {self.tire_change}")
        print(f"Repairs: {self.repairs}")
        print(f"{'='*40}\n")
