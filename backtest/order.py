from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class Order:
    action: Literal["enter", "exit"]
    quantity: Optional[float] = None  # Quantity of assets to be traded
    value: Optional[float] = None  # Alternatively, the nominal value to be traded
    price: Optional[float] = (
        None  # Strike price of a limit order. Optional, empty for a market order
    )
    position_id: Optional[str] = (
        None  # ID of the position to be closed. Needed for closing only
    )
