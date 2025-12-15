from __future__ import annotations

import argparse

from backtester.core.datafeed import DataFeed
from backtester.core.engine import Engine
from backtester.core.enums import ExecutionMode
from backtester.core.settings import BacktestSettings
from backtester.core.strategy_base import Strategy
from backtester.strategies.buy_and_hold import BuyAndHold
from backtester.strategies.ma_cross import MovingAverageCross
from backtester.strategies.donchian_breakout import DonchianBreakout


def main() -> None:
    """CLI-обёртка вокруг движка бэктестера."""
    p = argparse.ArgumentParser(description="Simple Backtester MVP")
    p.add_argument(
        "--csv",
        required=True,
        help="Path to CSV with columns: datetime,open,high,low,close[,volume]",
    )
    p.add_argument(
        "--strategy",
        choices=["bh", "ma", "donchian"],
        default="ma",
        help=(
            "bh=Buy&Hold, ma=Moving Average Cross, "
            "donchian=Donchian breakout"
        ),
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

    args = p.parse_args()

    feed = DataFeed.load_csv(args.csv)
    eng = Engine()

    strat: Strategy
    if args.strategy == "bh":
        strat = BuyAndHold()
    elif args.strategy == "ma":
        strat = MovingAverageCross(fast=args.fast, slow=args.slow)
    else:
        strat = DonchianBreakout(window=args.donchian_window)

    eng.set_data(feed)
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

    print("\n=== METRICS ===")
    for k, v in result.metrics.items():
        if isinstance(v, (int, float)):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")

    print("\n=== TRADES (dt, side, price, qty, commission) ===")
    for t in result.trades:
        print(
            f"{t.dt.isoformat()}, {t.side.value}, "
            f"{t.price:.4f}, {t.qty:.6f}, {t.commission:.6f}"
        )

    # сохраним equity_curve в CSV рядом
    out_path = "equity_curve.csv"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("datetime,equity\n")
        for dt, eq in result.equity_curve:
            f.write(f"{dt},{eq:.6f}\n")
    print(f"\nEquity curve saved to: {out_path}")


if __name__ == "__main__":
    main()
