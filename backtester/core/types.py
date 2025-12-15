from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import List
from .enums import ActionSide, TradeSide
from .errors import ValidationError

@dataclass(slots=True)
class Bar:
    dt: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    def __post_init__(self) -> None:
        if not isinstance(self.dt, datetime):
            raise ValidationError("Bar.dt must be datetime")
        for name in ("open", "high", "low", "close", "volume"):
            val = getattr(self, name)
            if not isinstance(val, (int,float)):
                raise ValidationError(f"Bar.{name} must be float-like")

@dataclass(slots=True)
class Trade:
    dt: datetime
    side: TradeSide
    price: float
    qty: float
    commission: float = 0.0
    def __post_init__(self) -> None:
        if not isinstance(self.dt, datetime):
            raise ValidationError("Trade.dt must be datetime")
        if not isinstance(self.side, TradeSide):
            raise ValidationError("Trade.side must be TradeSide")
        if self.price <= 0:
            raise ValidationError("Trade.price must be > 0")
        if self.qty <= 0:
            raise ValidationError("Trade.qty must be > 0")
        if self.commission < 0:
            raise ValidationError("Trade.commission must be >= 0")

@dataclass(slots=True)
class Action:
    side: ActionSide
    qty_hint: float = 0.0
    comment: str = ""
    def __post_init__(self) -> None:
        if self.qty_hint < 0:
            raise ValidationError("Action.qty_hint must be >= 0")

@dataclass(slots=True)
class TimeSeries:
    t: List[datetime]
    v: List[float]
    def __post_init__(self) -> None:
        if len(self.t) != len(self.v):
            raise ValidationError("TimeSeries.t and TimeSeries.v must be equal length")

__all__ = ["Bar","Trade","Action","TimeSeries"]
