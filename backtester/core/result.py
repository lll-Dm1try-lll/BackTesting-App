from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple

from .types import Trade, TimeSeries
from .settings import BacktestSettings


@dataclass(slots=True)
class BacktestResult:
    """
    Результат прогона бэктеста.

    metrics
        Сводные числовые метрики (start_equity, end_equity, profit и т.п.).

    trades
        Список совершённых сделок.

    equity_curve
        История equity во времени в виде списка кортежей (dt, equity).

    settings
        Настройки бэктеста, с которыми был запущен прогон.

    series
        Дополнительные временные ряды (например, equity как TimeSeries),
        доступные по строковым ключам.
    """

    metrics: Dict[str, float]
    trades: List[Trade]
    equity_curve: List[Tuple[datetime, float]]
    settings: BacktestSettings
    series: Dict[str, TimeSeries] = field(default_factory=dict)


__all__ = ["BacktestResult"]
