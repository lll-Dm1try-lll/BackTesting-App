from __future__ import annotations

class BacktestError(Exception):
    pass

class ValidationError(BacktestError):
    pass

__all__ = ["BacktestError", "ValidationError"]
