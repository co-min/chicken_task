from __future__ import annotations
from dataclasses import dataclass, field
import time


@dataclass
class RoundEvent:
    event_type: str
    round_num: int
    user_score: int
    pc_score: int
    token_positions: dict
    difficulty_index: int
    note: str = ''
    timestamp: float = field(default_factory=time.time)
