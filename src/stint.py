from dataclasses import dataclass, field
from typing import List, Optional
from src.utils import format_time
import json

@dataclass
class Stint:
    """Stint Start Values:"""

    stint_id: int
    driver_name: str
    start_time: float
    start_position: int
    start_incidents: int
    start_fuel: float
    start_fast_repairs: int
    laps: List[float] = field(default_factory=list)
    final: bool = False
    """Stint End Values:"""
    stint_length: Optional[float] = -1.0
    incidents: int = field(init=False)
    end_position: Optional[int] = -1
    end_fast_repairs: int = field(init=False)

    def __post_init__(self):
        self.incidents = self.start_incidents
        self.end_fast_repairs = self.start_fast_repairs

    """Pit Values:"""
    end_fuel: Optional[float] = None
    refuel_amount: Optional[float] = None
    required_repair_time: Optional[float] = None
    optional_repair_time: Optional[float] = None
    pit_service_duration: Optional[float] = 0.0
    pit_service_start_time: Optional[float] = None
    tire_change: Optional[bool] = False
    repairs: Optional[bool] = False

    def get_avg_lap(self) -> float:
        if self.laps:
            return sum(self.laps) / len(self.laps)
        return None

    def get_fastest_lap(self) -> float:
        if self.laps:
            return min(self.laps)
        return None

    def get_laps_completed(self) -> int:
        return len(self.laps)

    def get_in_lap(self) -> float:
        if self.laps and not self.final:
            return self.laps[-1]
        return None

    def get_out_lap(self) -> float:
        if self.laps:
            return self.laps[0]
        return None

    def end_stint(
        self,
        session_time: float,
        position: float,
        incidents: int,
        fast_repairs: int,
        end_fuel: float,
        final: bool,
    ) -> None:
        self.final = final
        self.stint_length = session_time - self.start_time
        self.end_position = position
        self.incidents = incidents - self.start_incidents
        self.end_fast_repairs = fast_repairs

        if self.final:
            self.end_fuel = end_fuel
        else:
            self.repairs = self._check_repairs()
            self.pit_service_duration = session_time - self.pit_service_start_time
        self.laps_completed = len(self.laps)

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
        if self.end_fast_repairs - self.start_fast_repairs > 0:
            return True
        elif self.optional_repair_time is None and self.required_repair_time is None:
            return None
        else:
            return (
                (self.optional_repair_time or 0.0) + (self.required_repair_time + 0.0)
            ) > 0.0

    def record_lap(self, lap_time: float) -> None:
        self.laps.append(lap_time)

    def to_dict(self) -> dict:
        return {
            "driver": self.driver_name,
            "start_time": self.start_time,
            "stint_length": self.stint_length,
            "laps_completed": self.get_laps_completed(),
            "avg_lap": self.get_avg_lap(),
            "fastest_lap": self.get_fastest_lap(),
            "out_lap": self.get_out_lap(),
            "in_lap": self.get_in_lap(),
            "start_fuel": self.start_fuel,
            "end_fuel": self.end_fuel,
            "refuel_amount": self.refuel_amount,
            "tire_change": self.tire_change,
            "repairs": self.repairs,
            "pit_service_duration": self.pit_service_duration,
            "incidents": self.incidents,
            "start_position": self.start_position,
            "end_position": self.end_position,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    

    # TODO: fix display output to work with None
    def display(self):
        """Print all values in the stint for easy review."""
        print(f"{' '*17}Stint {self.stint_id}")
        print(f"{'='*40}")
        print(f"Driver: {self.driver_name}")
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
        out = self.get_out_lap()
        print(f"Out Lap: {format_time(out) if out > 0.0 else 'N/A'}")
        inl = self.get_in_lap()
        print(f"In Lap: {format_time(inl) if inl > 0.0 else 'N/A'}")
        avg = self.get_avg_lap()
        print(f"Average Lap: {format_time(avg) if avg > 0.0 else 'N/A'}")
        print(f"Laps Completed: {self.get_laps_completed()}")
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
