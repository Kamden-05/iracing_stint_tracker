from dataclasses import dataclass, asdict

@dataclass
class Lap:
    stint_id: int
    number: int
    time: float

    def to_dict(self):
        return asdict(self)