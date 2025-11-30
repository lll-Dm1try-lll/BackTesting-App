from __future__ import annotations

from dataclasses import dataclass

from .enums import ExecutionMode
from .errors import ValidationError


@dataclass(slots=True)
class BacktestSettings:
    initial_cash: float = 10_000.0
    commission_pct: float = 0.0
    execution_mode: ExecutionMode = ExecutionMode.ON_CLOSE
    lot_size: float = 1.0  # шаг количества (1.0 = целые единицы)

    def __post_init__(self) -> None:
        if self.initial_cash <= 0:
            raise ValidationError("initial_cash must be > 0")
        if self.commission_pct < 0:
            raise ValidationError("commission_pct must be >= 0")
        if self.lot_size <= 0:
            raise ValidationError("lot_size must be > 0")
