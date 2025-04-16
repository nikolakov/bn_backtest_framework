from abc import ABC, abstractmethod
from typing import List
import pandas as pd
from order import Order
from positions_book import PositionsBook


class Strategy(ABC):
    """
    Abstract base class for trading strategies.
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def on_candle(
        self, data: pd.DataFrame, positions_book: PositionsBook
    ) -> List[Order]:
        """
        Callback function to be called at each step of the backtest.
        """
        pass
