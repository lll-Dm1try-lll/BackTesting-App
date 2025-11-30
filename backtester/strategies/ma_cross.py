from __future__ import annotations

from typing import List, Optional

from backtester.core.enums import ActionSide
from backtester.core.strategy_base import StrategyContext
from backtester.core.types import Action


def sma(values: List[float], period: int) -> Optional[float]:
    """Простое скользящее среднее по последним period значениям."""
    if len(values) < period:
        return None
    window = values[-period:]
    return sum(window) / float(period)


class MovingAverageCross:
    """
    Стратегия пересечения двух скользящих средних:
    - fast: короткая SMA
    - slow: длинная SMA
    """

    name = "MA Cross"

    def __init__(self, fast: int = 5, slow: int = 10) -> None:
        if fast <= 0 or slow <= 0 or fast >= slow:
            fast, slow = 5, 10
        self.fast = fast
        self.slow = slow
        self._closes: List[float] = []

    def warmup(self) -> int:
        # Стратегия сама контролирует готовность через sma(...).
        return 0

    def on_bar(self, ctx: StrategyContext) -> Action:
        self._closes.append(ctx.price("close"))
        f = sma(self._closes, self.fast)
        s = sma(self._closes, self.slow)
        if f is None or s is None:
            return Action(ActionSide.HOLD, 0.0)
        in_pos = ctx.position_size() > 0
        if not in_pos and f > s:
            return Action(ActionSide.BUY, 0.0, "fast>slow")
        if in_pos and f < s:
            return Action(ActionSide.SELL, 0.0, "fast<slow")
        return Action(ActionSide.HOLD, 0.0)
