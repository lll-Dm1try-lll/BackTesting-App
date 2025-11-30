from __future__ import annotations
from enum import Enum

class ExecutionMode(Enum):
    ON_CLOSE = "on_close"
    ON_NEXT_OPEN = "on_next_open"

class ActionSide(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class TradeSide(Enum):
    BUY = "buy"
    SELL = "sell"

class ParamType(Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"

__all__ = ["ExecutionMode", "ActionSide", "TradeSide", "ParamType"]
