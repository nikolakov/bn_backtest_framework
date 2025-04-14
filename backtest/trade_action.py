from dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class TradeAction:
    action: Literal['enter', 'exit']
    quantity: Optional[float] = None # needed for opening only
    value: Optional[float] = None # needed for opening only
    position_id: Optional[str] = None  # needed for closing only