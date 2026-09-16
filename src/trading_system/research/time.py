"""Shared timestamp validation for point-in-time research contracts."""

from __future__ import annotations

from datetime import datetime, timedelta


def require_utc(value: datetime, *, name: str) -> datetime:
    """Return *value* after verifying it is an aware UTC timestamp.

    The function intentionally does not convert timestamps. A caller that
    supplied a naive or non-UTC timestamp must correct its own data rather than
    having a research boundary silently changed.
    """
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be timezone-aware UTC")
    return value
