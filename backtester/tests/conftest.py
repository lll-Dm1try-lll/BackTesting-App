from __future__ import annotations

import sys
from pathlib import Path

# tests/ -> backtester/ -> (родитель с модулем backtester)
ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent

# Добавляем родительскую директорию, где лежит пакет backtester
parent_str = str(PARENT)
if parent_str not in sys.path:
    sys.path.insert(0, parent_str)
