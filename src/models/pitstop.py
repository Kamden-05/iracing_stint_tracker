from dataclasses import dataclass
from typing import Optional

@dataclass
class PitStop:

    stint_id: int
    road_enter_time: Optional[float] = None

    service_start_time: Optional[float] = None
    fuel_start_amount: Optional[float] = None
    required_repair_time: Optional[float] = None
    optional_repair_time: Optional[float] = None
    fuel_end_amount: Optional[float] = None
    service_end_time: Optional[float] = None
    road_exit_time: Optional[float] = None

    # tires
    left_front: Optional[bool] = None
    right_front: Optional[bool] = None
    left_rear: Optional[bool] = None
    right_rear: Optional[bool] = None

    @property
    def has_repairs(self) -> bool:
        return (self.required_repair_time or 0.0) + (
            self.optional_repair_time or 0.0
        ) > 0.0

    @property
    def has_tire_change(self) -> bool:
        return any(
            t is True
            for t in [
                self.left_front,
                self.right_front,
                self.left_rear,
                self.right_rear,
            ]
        )

    @property
    def pit_duration(self) -> Optional[float]:
        if self.road_exit_time is None:
            return None
        return self.road_exit_time - self.road_enter_time

    @property
    def box_time(self) -> Optional[float]:
        if self.service_end_time is None or self.service_start_time is None:
            return None
        return self.service_end_time - self.service_start_time

    def post_dict(self) -> dict:
        return {
            "stint_id": self.stint_id,
            "road_enter_time": self.road_enter_time,
            "service_start_time": self.service_start_time,
            "fuel_start_amount": self.fuel_start_amount,
            "repairs": self.has_repairs,
            "tire_change": self.has_tire_change,
        }

    def patch_dict(self) -> dict:
        return {
            "stint_id": self.stint_id,
            "service_end_time": self.service_end_time,
            "fuel_end_amount": self.fuel_end_amount,
            "road_exit_time": self.road_exit_time,
        }
