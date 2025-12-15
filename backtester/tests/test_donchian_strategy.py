from __future__ import annotations

from datetime import datetime, timedelta

from backtester.core.datafeed import DataFeed
from backtester.core.engine import Engine
from backtester.core.enums import TradeSide
from backtester.core.settings import BacktestSettings
from backtester.core.types import Bar
from backtester.strategies.donchian_breakout import DonchianBreakout


def _feed_from_closes(closes: list[float]) -> DataFeed:
    """Утилита для сборки DataFeed из списка цен закрытия."""
    base = datetime(2020, 1, 1)
    bars: list[Bar] = []
    for i, c in enumerate(closes):
        dt = base + timedelta(days=i)
        # Для простоты все OHLC равны цене закрытия.
        bars.append(
            Bar(dt=dt, open=c, high=c, low=c, close=c, volume=0.0)
        )
    feed = DataFeed(bars)
    feed.sort_and_validate()
    return feed


def test_donchian_breakout_enters_and_exits() -> None:
    """
    На простой растущей последовательности стратегия должна:
    - один раз войти в длинную позицию (BUY);
    - быть принудительно выведенной из позиции на последнем баре (SELL);
    - не потерять деньги.
    """
    # 100 пять дней, затем рост до 140 и небольшая коррекция.
    closes = [100.0, 100.0, 100.0, 100.0, 100.0,
              110.0, 120.0, 130.0, 140.0, 130.0]
    feed = _feed_from_closes(closes)

    eng = Engine()
    eng.set_data(feed)
    eng.set_strategy(DonchianBreakout(window=3))
    eng.configure(BacktestSettings(initial_cash=1000.0))

    result = eng.run()

    # Ожидаем одну покупку и один выход (авто-выход движка на последнем баре).
    assert len(result.trades) == 2
    assert result.trades[0].side is TradeSide.BUY
    assert result.trades[-1].side is TradeSide.SELL
    assert result.metrics["end_equity"] >= result.metrics["start_equity"]


def test_donchian_breakout_no_trades_on_flat_market() -> None:
    """
    Если рынок стоит "в боковике" и нет пробоев канала, стратегия
    не должна совершать сделок.
    """
    closes = [100.0] * 20
    feed = _feed_from_closes(closes)

    eng = Engine()
    eng.set_data(feed)
    eng.set_strategy(DonchianBreakout(window=5))
    eng.configure(BacktestSettings(initial_cash=1000.0))

    result = eng.run()

    assert result.trades == []
    assert result.metrics["end_equity"] == result.metrics["start_equity"]
