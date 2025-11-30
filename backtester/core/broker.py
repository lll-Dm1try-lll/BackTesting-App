from __future__ import annotations

from typing import List

from .datafeed import DataFeed
from .enums import ActionSide, ExecutionMode, TradeSide
from .types import Action, Trade


class Broker:
    """
    Простейший брокер: long-only, рыночные ордера,
    процентная комиссия и округление количества по шагу лота.
    """

    def __init__(
        self,
        commission_pct: float = 0.0,
        exec_mode: ExecutionMode = ExecutionMode.ON_CLOSE,
        lot_size: float = 1.0,
    ) -> None:
        self._commission_pct = float(commission_pct)
        self._exec_mode = exec_mode
        self._lot_size = float(lot_size)
        self._cash: float = 0.0
        self._position_qty: float = 0.0
        self._entry_price: float = 0.0
        self._trades: List[Trade] = []

    def reset(self, initial_cash: float, lot_size: float | None = None) -> None:
        self._cash = float(initial_cash)
        self._position_qty = 0.0
        self._entry_price = 0.0
        self._trades.clear()
        if lot_size is not None:
            self._lot_size = float(lot_size)

    # read-only interface
    def get_cash(self) -> float:
        return self._cash

    def get_position_qty(self) -> float:
        return self._position_qty

    def get_trades(self) -> List[Trade]:
        return list(self._trades)

    def _price_for_exec(self, i: int, feed: DataFeed) -> float:
        bar = feed.get(i)
        return bar.close if self._exec_mode is ExecutionMode.ON_CLOSE else bar.open

    def execute(self, act: Action, i: int, feed: DataFeed) -> Trade | None:
        if act.side is ActionSide.HOLD:
            return None
        price = self._price_for_exec(i, feed)
        dt = feed.get(i).dt

        if act.side is ActionSide.BUY:
            qty = self._desired_buy_qty(price, act.qty_hint)
            if qty <= 0:
                return None
            commission = price * qty * self._commission_pct
            cost = price * qty + commission
            if cost > self._cash + 1e-9:
                qty = self._shrink_qty_for_cash(price, qty)
                if qty <= 0:
                    return None
                commission = price * qty * self._commission_pct
                cost = price * qty + commission
            self._cash -= cost
            new_qty = self._position_qty + qty
            if new_qty > 0:
                self._entry_price = (self._entry_price * self._position_qty + price * qty) / new_qty
            self._position_qty = new_qty
            tr = Trade(dt=dt, side=TradeSide.BUY, price=price, qty=qty, commission=commission)
            self._trades.append(tr)
            return tr

        # SELL
        sellable = self._position_qty
        if sellable <= 0:
            return None
        qty = self._desired_sell_qty(act.qty_hint, sellable)
        if qty <= 0:
            return None
        commission = price * qty * self._commission_pct
        proceeds = price * qty - commission
        self._cash += proceeds
        self._position_qty -= qty
        if self._position_qty <= 0:
            self._position_qty = 0.0
            self._entry_price = 0.0
        tr = Trade(dt=dt, side=TradeSide.SELL, price=price, qty=qty, commission=commission)
        self._trades.append(tr)
        return tr

    def _desired_buy_qty(self, price: float, qty_hint: float) -> float:
        if qty_hint > 0:
            qty = qty_hint
        else:
            qty = self._cash / (price * (1.0 + self._commission_pct) + 1e-12)
        return self._round_qty(qty)

    def _shrink_qty_for_cash(self, price: float, qty: float) -> float:
        while qty > 0 and price * qty * (1.0 + self._commission_pct) - self._cash > 1e-9:
            qty -= self._lot_size
        return self._round_qty(max(qty, 0.0))

    def _desired_sell_qty(self, qty_hint: float, sellable: float) -> float:
        qty = sellable if qty_hint <= 0 else min(qty_hint, sellable)
        return self._round_qty(qty)

    def _round_qty(self, qty: float) -> float:
        if self._lot_size <= 0:
            return qty
        steps = qty / self._lot_size
        steps_floor = int(steps)
        return steps_floor * self._lot_size

    def mark_to_market(self, price: float) -> float:
        return self._cash + self._position_qty * price
