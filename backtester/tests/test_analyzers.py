from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from backtester.core.analyzers import DrawdownAnalyzer
from backtester.core.datafeed import DataFeed
from backtester.core.engine import Engine
from backtester.core.enums import ActionSide
from backtester.core.settings import BacktestSettings
from backtester.core.strategy_base import StrategyContext
from backtester.core.types import Action, Bar
from backtester.strategies.buy_and_hold import BuyAndHold


def _feed_from_closes(closes: list[float]) -> DataFeed:
    base = datetime(2020, 1, 1)
    bars = []
    for i, c in enumerate(closes):
        dt = base + timedelta(days=i)
        bars.append(Bar(dt=dt, open=c, high=c, low=c, close=c, volume=0.0))
    feed = DataFeed(bars)
    feed.sort_and_validate()
    return feed


class NoTradeStrategy:
    """Стратегия, которая никогда не торгует (всегда HOLD)."""

    name = "no-trade"

    def warmup(self) -> int:
        return 0

    def on_bar(self, ctx: StrategyContext) -> Action:
        return Action(ActionSide.HOLD, 0.0, "hold")


def test_drawdown_analyzer_no_trades() -> None:
    """При постоянной equity просадка должна быть нулевая."""
    feed = _feed_from_closes([100.0, 100.0, 100.0])
    eng = Engine()
    eng.set_data(feed)
    eng.set_strategy(NoTradeStrategy())
    eng.configure(BacktestSettings(initial_cash=1000.0))

    dd = DrawdownAnalyzer()
    eng.add_analyzer(dd)

    result = eng.run()

    assert result.metrics["max_drawdown"] == pytest.approx(0.0)
    assert result.metrics["max_drawdown_pct"] == pytest.approx(0.0)


def test_drawdown_analyzer_simple_drawdown() -> None:
    """
    Проверяем, что на простом сценарии с ростом и последующим падением
    просадка считается корректно.
    """
    # Цены: 100 -> 200 -> 50, BuyAndHold в начале:
    # qty = 10, equity: 1000 -> 2000 -> 500
    # max DD = 2000 - 500 = 1500 (75%)
    feed = _feed_from_closes([100.0, 200.0, 50.0])
    eng = Engine()
    eng.set_data(feed)
    eng.set_strategy(BuyAndHold())
    eng.configure(BacktestSettings(initial_cash=1000.0))

    dd = DrawdownAnalyzer()
    eng.add_analyzer(dd)

    result = eng.run()

    assert result.metrics["max_drawdown"] == pytest.approx(1500.0)
    assert result.metrics["max_drawdown_pct"] == pytest.approx(75.0)


def test_equity_series_matches_equity_curve() -> None:
    """
    Проверяем, что TimeSeries в BacktestResult.series["equity"]
    совпадает с equity_curve.
    """
    feed = _feed_from_closes([10.0, 11.0, 9.0])
    eng = Engine()
    eng.set_data(feed)
    eng.set_strategy(NoTradeStrategy())
    eng.configure(BacktestSettings(initial_cash=1000.0))

    result = eng.run()

    assert result.series is not None
    equity_ts = result.series.get("equity")
    assert equity_ts is not None

    times_from_curve = [dt for dt, _ in result.equity_curve]
    values_from_curve = [eq for _, eq in result.equity_curve]

    assert equity_ts.t == times_from_curve
    assert equity_ts.v == values_from_curve
