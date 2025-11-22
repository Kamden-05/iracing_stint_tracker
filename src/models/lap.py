from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Lap:
    stint_id: int
    number: int
    time: Optional[float] = None

    def to_post_json(self):
        return asdict(self)