from __future__ import annotations

from backtester.core.enums import ActionSide
from backtester.core.strategy_base import StrategyContext
from backtester.core.types import Action


class BuyAndHold:
    """Простейшая стратегия: один раз покупает и держит позицию до конца ряда."""

    name = "Buy & Hold"

    def warmup(self) -> int:
        return 0

    def on_bar(self, ctx: StrategyContext) -> Action:
        if ctx.position_size() <= 0:
            return Action(ActionSide.BUY, 0.0, "enter")
        return Action(ActionSide.HOLD, 0.0)
