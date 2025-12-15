from __future__ import annotations

import argparse
import cProfile
import pstats

from backtester.core.datafeed import DataFeed
from backtester.core.engine import Engine
from backtester.core.enums import ExecutionMode
from backtester.core.settings import BacktestSettings
from backtester.core.strategy_base import Strategy
from backtester.strategies.buy_and_hold import BuyAndHold
from backtester.strategies.ma_cross import MovingAverageCross
from backtester.strategies.donchian_breakout import DonchianBreakout


def _make_strategy(args: argparse.Namespace) -> Strategy:
    """
    Построить экземпляр стратегии по аргументам командной строки.
    Логика совпадает с CLI-бинарником.
    """
    if args.strategy == "bh":
        return BuyAndHold()
    if args.strategy == "ma":
        return MovingAverageCross(fast=args.fast, slow=args.slow)
    return DonchianBreakout(window=args.donchian_window)


def _run_backtest(args: argparse.Namespace) -> None:
    """
    Запустить один прогон бэктеста и вывести краткие метрики.
    Используется как «нагрузка» для профилирования.
    """
    feed = DataFeed.load_csv(args.csv)

    eng = Engine()
    eng.set_data(feed)

    strat = _make_strategy(args)
    eng.set_strategy(strat)

    eng.configure(
        BacktestSettings(
            initial_cash=args.cash,
            commission_pct=args.commission,
            execution_mode=ExecutionMode(args.mode),
            lot_size=args.lot,
        )
    )

    result = eng.run()

    print("\n=== METRICS (profiling run) ===")
    for k, v in result.metrics.items():
        if isinstance(v, (int, float)):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")


def main() -> None:
    """
    Точка входа для профилирования бэктеста.

    Пример запуска:

        python -m backtester.profile_backtest \\
          --csv backtester/data/AAPL_5Y.csv \\
          --strategy ma \\
          --fast 5 --slow 10 \\
          --cash 10000 \\
          --commission 0.0 \\
          --mode on_close \\
          --lot 1.0 \\
          --sort cumulative \\
          --lines 30
    """
    p = argparse.ArgumentParser(description="Profile backtester performance")
    p.add_argument(
        "--csv",
        required=True,
        help="Path to CSV with columns: datetime,open,high,low,close[,volume]",
    )
    p.add_argument(
        "--strategy",
        choices=["bh", "ma", "donchian"],
        default="ma",
        help="bh=Buy&Hold, ma=Moving Average Cross, donchian=Donchian breakout",
    )
    p.add_argument("--fast", type=int, default=5, help="MA fast (for ma)")
    p.add_argument("--slow", type=int, default=10, help="MA slow (for ma)")
    p.add_argument(
        "--donchian-window",
        type=int,
        default=20,
        help="Window for Donchian breakout (for strategy=donchian)",
    )
    p.add_argument("--cash", type=float, default=10_000.0, help="Initial cash")
    p.add_argument(
        "--commission",
        type=float,
        default=0.0,
        help="Commission, fraction (e.g. 0.001 = 0.1%)",
    )
    p.add_argument(
        "--mode",
        choices=["on_close", "on_next_open"],
        default="on_close",
        help="Execution mode",
    )
    p.add_argument(
        "--lot",
        type=float,
        default=1.0,
        help="Lot size step (e.g. 1 for whole units, 0.1 for tenths)",
    )
    p.add_argument(
        "--sort",
        choices=["time", "cumulative"],
        default="cumulative",
        help="Поле сортировки в отчёте cProfile (time или cumulative).",
    )
    p.add_argument(
        "--lines",
        type=int,
        default=30,
        help="Сколько строк показывать в выводе профилировщика.",
    )

    args = p.parse_args()

    profiler = cProfile.Profile()
    profiler.enable()
    _run_backtest(args)
    profiler.disable()

    stats = pstats.Stats(profiler).strip_dirs().sort_stats(args.sort)

    print(f"\n=== cProfile stats (top {args.lines}) ===")
    stats.print_stats(args.lines)


if __name__ == "__main__":
    main()
