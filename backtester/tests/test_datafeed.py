from __future__ import annotations

from datetime import datetime
from textwrap import dedent

from backtester.core.datafeed import DataFeed
from backtester.core.errors import ValidationError


def test_datafeed_simple_csv(tmp_path) -> None:
    csv_content = dedent(
        """\
        datetime,open,high,low,close,volume
        2025-01-01,1,2,0.5,1.5,1000
        2025-01-02,1.5,2.5,1.0,2.0,1500
        """
    )
    path = tmp_path / "simple.csv"
    path.write_text(csv_content, encoding="utf-8")

    feed = DataFeed.load_csv(str(path))
    assert feed.size() == 2
    b0 = feed.get(0)
    b1 = feed.get(1)
    assert b0.dt < b1.dt
    assert b0.open == 1.0
    assert b1.close == 2.0


def test_datafeed_nasdaq_format(tmp_path) -> None:
    csv_content = dedent(
        """\
        Date,Close/Last,Volume,Open,High,Low
        11/28/2025,$278.85,20,135,620,$277.26,$279.00,$275.9865
        """
    ).replace("20,135,620", "20135620")

    path = tmp_path / "nasdaq.csv"
    path.write_text(csv_content, encoding="utf-8")

    feed = DataFeed.load_csv(str(path))
    assert feed.size() == 1
    bar = feed.get(0)
    assert bar.dt.year == 2025
    assert bar.open == 277.26
    assert bar.high == 279.00
    assert bar.low == 275.9865
    assert bar.close == 278.85
    assert bar.volume == 20135620.0


def test_datafeed_missing_columns(tmp_path) -> None:
    csv_content = dedent(
        """\
        datetime,open,close
        2025-01-01,1,1.5
        """
    )
    path = tmp_path / "bad.csv"
    path.write_text(csv_content, encoding="utf-8")

    try:
        DataFeed.load_csv(str(path))
    except ValidationError:
        pass
    else:
        raise AssertionError("Expected ValidationError for missing columns")
