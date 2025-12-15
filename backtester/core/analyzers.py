from __future__ import annotations

from datetime import datetime
from typing import Dict, Protocol


class Analyzer(Protocol):
    """
    Базовый контракт для анализаторов результатов бэктеста.

    Анализатор вызывается на каждом баре с текущей датой и equity,
    а в конце бэктеста возвращает набор метрик, которые попадают
    в BacktestResult.metrics.
    """

    name: str

    def on_bar(self, dt: datetime, equity: float) -> None:
        """Обновить внутреннее состояние анализатора на очередном баре."""
        ...

    def finalize(self) -> Dict[str, float]:
        """
        Вернуть словарь метрик, которые будут добавлены
        в BacktestResult.metrics.
        """
        ...


class DrawdownAnalyzer:
    """
    Анализатор просадки по equity.

    Считает максимальную абсолютную просадку и максимальную
    относительную просадку (в процентах от предыдущего максимума).
    """

    name = "drawdown"

    def __init__(self) -> None:
        self._peak: float | None = None
        self._max_drawdown: float = 0.0
        self._max_drawdown_pct: float = 0.0

    def on_bar(self, dt: datetime, equity: float) -> None:
        if self._peak is None or equity > self._peak:
            self._peak = equity
            return

        peak = self._peak
        if peak <= 0.0:
            return

        drawdown = peak - equity
        if drawdown > self._max_drawdown:
            self._max_drawdown = drawdown
            self._max_drawdown_pct = drawdown / peak * 100.0

    def finalize(self) -> Dict[str, float]:
        return {
            "max_drawdown": self._max_drawdown,
            "max_drawdown_pct": self._max_drawdown_pct,
        }


__all__ = ["Analyzer", "DrawdownAnalyzer"]
