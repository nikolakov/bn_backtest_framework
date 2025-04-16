# Possibly to be renamed to position, while current positions get renamed to Trades

from typing import List

import pandas as pd

from position import Position
from order import Order


class PositionsBook:
    """
    Class to expose an API for managing open positions.
    """

    def __init__(self, positions: List[Position], current_data: pd.Series):
        self._positions = positions
        self._current_data = current_data

    @property
    def open_positions(self) -> List[Position]:
        """
        Returns a list of open positions.
        """
        return [pos for pos in self._positions if pos.is_open]

    @property
    def closed_positions(self) -> List[Position]:
        """
        Returns a list of closed positions.
        """
        return [pos for pos in self._positions if pos.is_closed]

    @property
    def quantity(self) -> float:
        """
        Returns the total quantity of all open positions.
        """
        return sum(pos.quantity for pos in self.open_positions)

    @property
    def value(self) -> float:
        """
        Returns the total value of all open positions.
        """
        return sum(
            pos.quantity * self._current_data["Close"] for pos in self.open_positions
        )

    @property
    def is_long(self) -> bool:
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        return self.quantity < 0

    @property
    def is_flat(self) -> bool:
        return self.quantity == 0

    def close(self) -> List[Order]:
        """
        Returns a list of orders to close all open positions.
        """
        return [
            Order(
                action="exit",
                position_id=pos.id,
            )
            for pos in self.open_positions
        ]
