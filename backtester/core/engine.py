from __future__ import annotations

from datetime import datetime
from typing import List, Tuple

from .analyzers import Analyzer, DrawdownAnalyzer
from .broker import Broker
from .datafeed import DataFeed
from .enums import ActionSide, ExecutionMode
from .context import Context
from .result import BacktestResult
from .settings import BacktestSettings
from .types import Action, TimeSeries


class Engine:
    """Движок бэктестера: склеивает DataFeed, Strategy, Broker и анализаторы."""

    def __init__(self) -> None:
        self._feed: DataFeed | None = None
        self._broker: Broker | None = None
        self._strategy = None
        self._settings = BacktestSettings()
        self._analyzers: List[Analyzer] = []
        # По умолчанию подключаем анализатор просадки, чтобы базовый набор
        # метрик включал max_drawdown и max_drawdown_pct.
        self.add_analyzer(DrawdownAnalyzer())

    def set_data(self, feed: DataFeed) -> None:
        """Задать источник данных (ряды OHLCV)."""
        self._feed = feed

    def set_strategy(self, strategy) -> None:
        """Задать торговую стратегию."""
        self._strategy = strategy

    def configure(self, settings: BacktestSettings) -> None:
        """Задать настройки бэктеста и переинициализировать брокера."""
        self._settings = settings
        self._broker = Broker(
            commission_pct=settings.commission_pct,
            exec_mode=settings.execution_mode,
            lot_size=settings.lot_size,
        )

    def add_analyzer(self, analyzer: Analyzer) -> None:
        """Добавить анализатор, который будет вызываться на каждом баре."""
        self._analyzers.append(analyzer)

    def clear_analyzers(self) -> None:
        """Удалить все привязанные к движку анализаторы."""
        self._analyzers.clear()

    def run(self) -> BacktestResult:
        """Запустить один прогон бэктеста и вернуть агрегированный результат."""
        assert self._feed is not None, "DataFeed not set"
        assert self._strategy is not None, "Strategy not set"
        assert self._broker is not None, "Broker not configured"

        feed = self._feed
        broker = self._broker
        broker.reset(self._settings.initial_cash, self._settings.lot_size)
        ctx = Context(feed, broker)

        warmup = max(0, self._strategy.warmup())
        n = feed.size()
        start_equity = self._settings.initial_cash

        if n == 0 or warmup >= n:
            # Нет данных или warmup «съел» все бары
            metrics = {
                "start_equity": start_equity,
                "end_equity": start_equity,
                "profit": 0.0,
                "return_pct": 0.0,
                "trades": 0.0,
            }
            # Анализаторы не вызываются (нет баров), но финализируем их,
            # чтобы они могли вернуть свои нулевые метрики.
            for analyzer in self._analyzers:
                metrics.update(analyzer.finalize())

            return BacktestResult(
                metrics=metrics,
                trades=[],
                equity_curve=[],
                settings=self._settings,
                series={},  # при отсутствии данных series остаётся пустым
            )

        pending: Action | None = None
        equity_curve: List[Tuple[datetime, float]] = []

        for i in range(warmup, n):
            if (
                self._settings.execution_mode is ExecutionMode.ON_NEXT_OPEN
                and pending is not None
            ):
                broker.execute(pending, i, feed)
                pending = None

            ctx.set_index(i)
            act: Action = self._strategy.on_bar(ctx)

            if self._settings.execution_mode is ExecutionMode.ON_CLOSE:
                broker.execute(act, i, feed)
            else:
                pending = None if act.side is ActionSide.HOLD else act

            if i == n - 1 and broker.get_position_qty() > 0:
                broker.execute(
                    Action(ActionSide.SELL, 0.0, "auto-exit"),
                    i,
                    feed,
                )

            bar = feed.get(i)
            eq = broker.get_cash() + broker.get_position_qty() * bar.close
            equity_curve.append((bar.dt, eq))

            for analyzer in self._analyzers:
                analyzer.on_bar(bar.dt, eq)

        end_equity = equity_curve[-1][1] if equity_curve else start_equity
        profit = end_equity - start_equity
        ret_pct = (profit / start_equity * 100.0) if start_equity else 0.0

        metrics = {
            "start_equity": start_equity,
            "end_equity": end_equity,
            "profit": profit,
            "return_pct": ret_pct,
            "trades": float(len(broker.get_trades())),
        }

        for analyzer in self._analyzers:
            metrics.update(analyzer.finalize())

        equity_ts = TimeSeries(
            t=[dt for dt, _ in equity_curve],
            v=[eq for _, eq in equity_curve],
        )

        return BacktestResult(
            metrics=metrics,
            trades=broker.get_trades(),
            equity_curve=equity_curve,
            settings=self._settings,
            series={"equity": equity_ts},
        )
