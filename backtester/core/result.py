from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

from .types import Trade
from .settings import BacktestSettings


@dataclass(slots=True)
class BacktestResult:
    metrics: Dict[str, float]
    trades: List[Trade]
    equity_curve: List[Tuple[datetime, float]]
    settings: BacktestSettings


__all__ = ["BacktestResult"]
