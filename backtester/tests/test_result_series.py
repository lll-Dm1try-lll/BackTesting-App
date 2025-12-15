from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from backtester.core.datafeed import DataFeed
from backtester.core.engine import Engine
from backtester.core.settings import BacktestSettings
from backtester.core.types import Bar
from backtester.strategies.buy_and_hold import BuyAndHold


def _feed_from_closes(closes: list[float]) -> DataFeed:
    """Утилита для сборки DataFeed из списка цен закрытия."""
    base = datetime(2020, 1, 1)
    bars: list[Bar] = []
    for i, c in enumerate(closes):
        dt = base + timedelta(days=i)
        bars.append(
            Bar(dt=dt, open=c, high=c, low=c, close=c, volume=0.0)
        )
    feed = DataFeed(bars)
    feed.sort_and_validate()
    return feed


def test_equity_series_matches_equity_curve() -> None:
    """
    Проверяем, что series["equity"] согласован с equity_curve:
    - те же временные метки;
    - те же значения equity.
    """
    closes = [100.0, 110.0, 120.0, 90.0]
    feed = _feed_from_closes(closes)

    eng = Engine()
    eng.set_data(feed)
    eng.set_strategy(BuyAndHold())
    eng.configure(BacktestSettings(initial_cash=1000.0))

    result = eng.run()

    assert "equity" in result.series

    ts = result.series["equity"]
    curve = result.equity_curve

    # Длины должны совпадать.
    assert len(ts.t) == len(curve)
    assert len(ts.v) == len(curve)

    # Каждая точка TimeSeries совпадает с equity_curve.
    for (dt_curve, eq_curve), dt_ts, eq_ts in zip(curve, ts.t, ts.v):
        assert dt_ts == dt_curve
        assert eq_ts == pytest.approx(eq_curve)


def test_series_empty_for_empty_feed() -> None:
    """
    При пустом фиде движок должен корректно вернуть пустую equity_curve
    и пустой словарь series.
    """
    feed = DataFeed(bars=[])
    feed.sort_and_validate()

    eng = Engine()
    eng.set_data(feed)
    eng.set_strategy(BuyAndHold())
    eng.configure(BacktestSettings(initial_cash=1000.0))

    result = eng.run()

    assert result.equity_curve == []
    assert result.series == {}
