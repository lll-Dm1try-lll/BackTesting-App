from __future__ import annotations

from datetime import datetime, timedelta

from backtester.core.datafeed import DataFeed
from backtester.core.engine import Engine
from backtester.core.enums import TradeSide
from backtester.core.settings import BacktestSettings
from backtester.core.types import Bar
from backtester.strategies.buy_and_hold import BuyAndHold
from backtester.strategies.ma_cross import MovingAverageCross


def _feed_from_closes(closes: list[float]) -> DataFeed:
    base = datetime(2020, 1, 1)
    bars = []
    for i, c in enumerate(closes):
        dt = base + timedelta(days=i)
        bars.append(Bar(dt=dt, open=c, high=c, low=c, close=c, volume=0.0))
    feed = DataFeed(bars)
    feed.sort_and_validate()
    return feed


def test_engine_buy_and_hold_single_round_trip() -> None:
    feed = _feed_from_closes([100.0, 105.0, 110.0, 115.0])
    eng = Engine()
    eng.set_data(feed)
    eng.set_strategy(BuyAndHold())
    eng.configure(BacktestSettings(initial_cash=1000.0))

    result = eng.run()

    # Должен быть один вход и один авто-выход на последнем баре
    assert len(result.trades) == 2
    assert result.trades[0].side is TradeSide.BUY
    assert result.trades[1].side is TradeSide.SELL
    assert result.metrics["end_equity"] > result.metrics["start_equity"]


def test_engine_ma_cross_trend_profit() -> None:
    # Трендовая последовательность для fast=2, slow=3:
    closes = [1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 4.5]
    feed = _feed_from_closes(closes)

    eng = Engine()
    eng.set_data(feed)
    eng.set_strategy(MovingAverageCross(fast=2, slow=3))
    eng.configure(BacktestSettings(initial_cash=1000.0))

    result = eng.run()

    # Должен быть хотя бы один вход и выход
    assert len(result.trades) >= 2
    assert result.trades[0].side is TradeSide.BUY
    assert result.trades[-1].side is TradeSide.SELL
    # На такой тривиальной трендовой серии стратегия не должна сливать в ноль
    assert result.metrics["end_equity"] >= result.metrics["start_equity"]
