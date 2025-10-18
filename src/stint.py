from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class Lap:
    pass


@dataclass
class Stint:
    """Stint Start Values:"""

    driver_name: str
    start_time: float
    start_position: int
    start_incidents: int
    start_fuel: float
    start_fast_repairs: int
    laps: List[Lap] = field(default_factory=list)

    """Stint End Values:"""
    end_incidents: int = -1
    end_fast_repairs: int = -1
    end_position: Optional[int] = None
    stint_length: Optional[float] = None
    final: bool = False

    def model_post_init(self):
        self.end_incidents = self.start_incidents
        self.end_fast_repairs = self.start_fast_repairs

    """Pit Values:"""
    end_fuel: Optional[float] = None
    refuel_amount: Optional[float] = None
    required_repair_time: Optional[float] = None
    optional_repair_time: Optional[float] = None
    pit_service_duration: Optional[float] = None
    pit_service_start_time: Optional[float] = None
    tire_change: Optional[bool] = None

    @property
    def avg_lap(self) -> Optional[float]:
        return (
            (sum(lap.time for lap in self.laps) / len(self.laps)) if self.laps else None
        )

    @property
    def fastest_lap(self) -> Optional[float]:
        return (min(lap.time for lap in self.laps)) if self.laps else None

    @property
    def laps_completed(self) -> int:
        return len(self.laps)

    @property
    def in_lap(self) -> Optional[float]:
        if self.laps and not self.final:
            return self.laps[-1].time
        return None

    @property
    def out_lap(self) -> Optional[float]:
        if self.laps:
            return self.laps[0].time
        return None

    def record_lap(self, time: float, lap_number: int) -> None:
        lap = Lap(stint_id=self.stint_id, time=time, number=lap_number)
        self.laps.append(lap)

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
        self.end_incidents = incidents
        self.end_fast_repairs = fast_repairs

        if self.final:
            self.end_fuel = end_fuel
        else:
            self.pit_service_duration = session_time - self.pit_service_start_time

    def record_pit(
        self,
        required_repair_time: float,
        optional_repair_time: float,
        end_fuel: float,
        refuel_amount: float,
        tires: bool,
        session_time: float,
    ) -> None:
        self.required_repair_time = required_repair_time
        self.optional_repair_time = optional_repair_time
        self.end_fuel = end_fuel
        self.refuel_amount = refuel_amount
        self.tire_change = tires
        self.pit_service_start_time = session_time

    @property
    def repairs(self) -> Optional[bool]:
        if self.end_fast_repairs - self.start_fast_repairs > 0:
            return True
        elif self.optional_repair_time is None and self.required_repair_time is None:
            return None
        else:
            return (
                (self.optional_repair_time or 0.0) + (self.required_repair_time or 0.0)
            ) > 0.0

    @property
    def incidents(self) -> int:
        return self.end_incidents - self.start_incidents
