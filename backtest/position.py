from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Position:
    id: str
    entry_time: datetime
    exit_time: Optional[datetime]
    quantity: float
