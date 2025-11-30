from __future__ import annotations

from datetime import datetime, timedelta

from backtester.core.broker import Broker
from backtester.core.datafeed import DataFeed
from backtester.core.enums import ActionSide, ExecutionMode, TradeSide
from backtester.core.types import Action, Bar


def _make_feed(prices: list[float]) -> DataFeed:
    base = datetime(2020, 1, 1)
    bars = []
    for i, p in enumerate(prices):
        dt = base + timedelta(days=i)
        bars.append(Bar(dt=dt, open=p, high=p, low=p, close=p, volume=0.0))
    feed = DataFeed(bars)
    feed.sort_and_validate()
    return feed


def test_broker_round_trip_no_commission() -> None:
    feed = _make_feed([100.0, 110.0])
    broker = Broker(commission_pct=0.0, exec_mode=ExecutionMode.ON_CLOSE, lot_size=1.0)
    broker.reset(initial_cash=1000.0)

    # BUY на первом баре
    buy = Action(ActionSide.BUY, 0.0, "enter")
    tr_buy = broker.execute(buy, 0, feed)
    assert tr_buy is not None
    assert tr_buy.side is TradeSide.BUY
    assert broker.get_position_qty() > 0

    # SELL на втором баре
    sell = Action(ActionSide.SELL, 0.0, "exit")
    tr_sell = broker.execute(sell, 1, feed)
    assert tr_sell is not None
    assert tr_sell.side is TradeSide.SELL
    assert broker.get_position_qty() == 0.0

    # equity после круговой сделки должна быть > начальной (цена выросла)
    end_cash = broker.get_cash()
    assert end_cash > 1000.0


def test_broker_commission_reduces_profit() -> None:
    feed = _make_feed([100.0, 100.0])
    broker = Broker(commission_pct=0.01, exec_mode=ExecutionMode.ON_CLOSE, lot_size=1.0)
    broker.reset(initial_cash=1000.0)

    buy = Action(ActionSide.BUY, 0.0, "enter")
    broker.execute(buy, 0, feed)

    sell = Action(ActionSide.SELL, 0.0, "exit")
    broker.execute(sell, 1, feed)

    # из-за комиссии после buy+sell кэш должен быть < начального
    assert broker.get_cash() < 1000.0
