from __future__ import annotations

from datetime import datetime

from .broker import Broker
from .datafeed import DataFeed
from .types import Bar


class Context:
    """Реализация StrategyContext для движка."""

    def __init__(self, feed: DataFeed, broker: Broker) -> None:
        self._feed = feed
        self._broker = broker
        self._i = 0

    def set_index(self, i: int) -> None:
        self._i = i

    def index(self) -> int:
        return self._i

    def bar(self) -> Bar:
        return self._feed.get(self._i)

    def time(self) -> datetime:
        return self.bar().dt

    def price(self, series: str = "close") -> float:
        b = self.bar()
        return getattr(b, series)

    def position_size(self) -> float:
        return self._broker.get_position_qty()

    def cash(self) -> float:
        return self._broker.get_cash()

    def equity(self) -> float:
        return self._broker.get_cash() + self._broker.get_position_qty() * self.price("close")
