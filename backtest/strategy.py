from abc import ABC, abstractmethod
from typing import List, Any
import pandas as pd
from trade_action import TradeAction
from position import Position

class Strategy(ABC):
    """
    Abstract base class for trading strategies.
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def on_candle(self, data: pd.DataFrame, positions_list: List[Position]) -> List[TradeAction]:
        """
        Callback function to be called at each step of the backtest.
        """
        pass