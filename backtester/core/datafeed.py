from __future__ import annotations

import csv
from datetime import datetime
from typing import List

from .errors import ValidationError
from .types import Bar


class DataFeed:
    """Источник баров OHLCV, загружаемый из CSV."""

    def __init__(self, bars: List[Bar], symbol: str = "", timeframe: str = "") -> None:
        self._bars = bars
        self.symbol = symbol
        self.timeframe = timeframe

    @staticmethod
    def load_csv(path: str, symbol: str = "", timeframe: str = "") -> "DataFeed":
        """
        Загрузка баров из CSV.

        Поддерживаемые варианты заголовков:

        * дата: ``datetime`` или ``Date``
        * цена закрытия: ``close`` или ``Close/Last``
        * остальные поля: ``open``, ``high``, ``low``, ``volume``

        Поддерживаемые форматы:

        * числовые значения могут содержать символ ``$`` и/или разделитель тысяч ``,``
          (например: ``278.85``, ``$278.85``, ``20,135,620``)
        * даты могут быть в форматах ``YYYY-MM-DD[ HH:MM:SS]`` или ``MM/DD/YYYY``
        """
        bars: List[Bar] = []

        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            fieldnames_lower = {name.lower() for name in fieldnames}

            # дата: datetime/date
            if "datetime" in fieldnames_lower:
                dt_col = "datetime"
            elif "date" in fieldnames_lower:
                dt_col = "date"
            else:
                raise ValidationError("CSV must contain 'datetime' or 'date' column")

            # цены: open/high/low обязательны
            required_price_cols = {"open", "high", "low"}
            missing_price = required_price_cols - fieldnames_lower
            if missing_price:
                raise ValidationError(f"CSV missing columns: {', '.join(sorted(missing_price))}")

            # close: поддерживаем close и close/last (как у nasdaq)
            if "close" in fieldnames_lower:
                close_col = "close"
            elif "close/last" in fieldnames_lower:
                close_col = "close/last"
            else:
                raise ValidationError("CSV must contain 'close' or 'Close/Last' column")

            for row in reader:
                # нормализуем ключи строки к lower()
                row_l = {k.lower(): v for k, v in row.items() if k is not None}

                dt_raw = row_l.get(dt_col)
                if not dt_raw:
                    raise ValidationError("CSV row has no datetime value")
                dt = DataFeed._parse_dt(dt_raw)

                try:
                    open_ = DataFeed._parse_number(row_l["open"])
                    high = DataFeed._parse_number(row_l["high"])
                    low = DataFeed._parse_number(row_l["low"])
                    close = DataFeed._parse_number(row_l[close_col])
                    volume = DataFeed._parse_number(row_l.get("volume", "0"))
                except KeyError as e:
                    raise ValidationError(f"Missing OHLC field in row: {e}") from e
                except ValueError as e:
                    raise ValidationError(f"Bad numeric value in row: {e}") from e

                bars.append(
                    Bar(
                        dt=dt,
                        open=open_,
                        high=high,
                        low=low,
                        close=close,
                        volume=volume,
                    )
                )

        feed = DataFeed(bars, symbol=symbol, timeframe=timeframe)
        feed.sort_and_validate()
        return feed

    @staticmethod
    def _parse_dt(val: str) -> datetime:
        """Парсинг даты: сначала ISO, затем 'YYYY-MM-DD HH:MM:SS', затем 'MM/DD/YYYY'."""
        val = val.strip()
        # ISO 8601: 2025-11-28 или 2025-11-28 00:00:00
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            pass

        # Явный формат с временем
        for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y"):
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                continue

        raise ValidationError(f"Bad datetime format: {val}")

    @staticmethod
    def _parse_number(val: str | float | int) -> float:
        """
        Парсинг чисел из строк вида:
        - "278.85"
        - "$278.85"
        - "20,135,620"
        - "$20,135,620"
        """
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        if not s:
            return 0.0
        if s.startswith("$"):
            s = s[1:]
        s = s.replace(",", "")
        return float(s)

    def get(self, i: int) -> Bar:
        return self._bars[i]

    def size(self) -> int:
        return len(self._bars)

    def sort_and_validate(self) -> None:
        self._bars.sort(key=lambda b: b.dt)
        seen = set()
        uniq: List[Bar] = []
        for b in self._bars:
            if b.dt not in seen:
                uniq.append(b)
                seen.add(b.dt)
        self._bars = uniq
