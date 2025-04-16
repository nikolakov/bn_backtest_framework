from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Position:
    id: str
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime]
    exit_price: Optional[float]
    quantity: float

    @property
    def is_open(self) -> bool:
        """
        Returns True if the position is open.
        """
        return self.exit_time is None

    @property
    def is_closed(self) -> bool:
        """
        Returns True if the position is closed.
        """
        return self.exit_time is not None

    @property
    def is_long(self) -> bool:
        """
        Returns True if the position is long.
        """
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """
        Returns True if the position is short.
        """
        return self.quantity < 0
