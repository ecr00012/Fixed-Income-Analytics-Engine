import calendar
from datetime import date


def act_act(start: date, end: date) -> float:
    """Actual/Actual day count fraction."""
    if start == end:
        return 0.0
    actual_days = (end - start).days
    days_in_year = 366 if calendar.isleap(start.year) else 365
    return actual_days / days_in_year


def thirty_360(start: date, end: date) -> float:
    """30/360 day count fraction."""
    if start == end:
        return 0.0
    d1 = min(start.day, 30)
    d2 = end.day if d1 < 30 else min(end.day, 30)
    days = (
        360 * (end.year - start.year)
        + 30 * (end.month - start.month)
        + (d2 - d1)
    )
    return days / 360


def act_360(start: date, end: date) -> float:
    """Actual/360 day count fraction."""
    if start == end:
        return 0.0
    actual_days = (end - start).days
    return actual_days / 360


_CONVENTIONS = {
    "ACT/ACT": act_act,
    "30/360": thirty_360,
    "ACT/360": act_360,
}


def day_count_fraction(start: date, end: date, convention: str) -> float:
    """Compute year fraction between two dates using the given convention."""
    func = _CONVENTIONS.get(convention)
    if func is None:
        raise ValueError(f"Unknown day count convention: {convention!r}")
    return func(start, end)
