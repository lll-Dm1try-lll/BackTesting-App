from __future__ import annotations

from typing import List

from backtester.core.enums import ActionSide
from backtester.core.strategy_base import StrategyContext
from backtester.core.types import Action


class DonchianBreakout:
    """
    Стратегия пробоя канала (Donchian breakout).

    Идея:
    - строим ценовой канал по максимумам/минимумам за окно `window` баров (по high/low);
    - входим в long, когда цена закрытия пробивает верхнюю границу канала;
    - выходим из позиции, когда цена закрытия опускается ниже нижней границы канала;
    - остальное время — HOLD.

    Канал считается по предыдущим барам (т. е. текущий бар в расчёт границ не входит).
    """

    name = "Donchian Breakout"

    def __init__(self, window: int = 20) -> None:
        if window <= 1:
            # Защита от некорректных параметров, используем дефолт.
            window = 20
        self.window = window
        self._highs: List[float] = []
        self._lows: List[float] = []

    def warmup(self) -> int:
        """
        Стратегия сама контролирует готовность по длине внутренних буферов.

        Возвращаем 0, чтобы движок не пропускал начальные бары целиком.
        """
        return 0

    def on_bar(self, ctx: StrategyContext) -> Action:
        """
        Основная логика стратегии на одном баре.

        - обновляем историю high/low;
        - если истории мало — HOLD;
        - строим канал по предыдущим `window` барам;
        - проверяем условия входа/выхода.
        """
        high = ctx.price("high")
        low = ctx.price("low")
        close = ctx.price("close")

        self._highs.append(high)
        self._lows.append(low)

        # Пока не накопили достаточно истории — ничего не делаем.
        if len(self._highs) <= self.window:
            return Action(ActionSide.HOLD, 0.0)

        # Канал строим по ПРЕДЫДУЩИМ барам, текущий бар не включаем.
        lookback_highs = self._highs[-(self.window + 1) : -1]
        lookback_lows = self._lows[-(self.window + 1) : -1]

        upper = max(lookback_highs)
        lower = min(lookback_lows)

        in_pos = ctx.position_size() > 0

        # Вход при пробое верхней границы.
        if not in_pos and close > upper:
            return Action(ActionSide.BUY, 0.0, "donchian_breakout_up")

        # Выход при пробое вниз нижней границы.
        if in_pos and close < lower:
            return Action(ActionSide.SELL, 0.0, "donchian_breakdown")

        return Action(ActionSide.HOLD, 0.0)


__all__ = ["DonchianBreakout"]
