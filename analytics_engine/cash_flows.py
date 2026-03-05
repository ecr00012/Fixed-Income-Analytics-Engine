from datetime import date
from dateutil.relativedelta import relativedelta

from analytics_engine.day_count import day_count_fraction


def generate_coupon_schedule(settlement: date, maturity: date, freq: int) -> list[date]:
    """
    Generate coupon payment dates from settlement (exclusive) to maturity (inclusive).
    Uses backward generation from maturity — the standard bond market convention.
    """
    if freq == 0:
        return []
    months_per_period = 12 // freq
    dates = []
    current = maturity
    while current > settlement:
        dates.append(current)
        current -= relativedelta(months=months_per_period)
    dates.sort()
    return dates


def compute_accrued_interest(
    settlement: date,
    coupon_rate: float,
    freq: int,
    day_count: str,
    prev_coupon: date | None,
    next_coupon: date | None,
) -> float:
    """
    Compute accrued interest (per 100 face value) from prev_coupon to settlement.
    Returns 0 for zero-coupon bonds or when settlement is on a coupon date.
    """
    if freq == 0 or coupon_rate == 0.0:
        return 0.0
    if prev_coupon is None or next_coupon is None:
        return 0.0
    if settlement == prev_coupon:
        return 0.0
    coupon_payment = coupon_rate / freq * 100  # per 100 face value
    accrued_fraction = day_count_fraction(prev_coupon, settlement, day_count) / day_count_fraction(
        prev_coupon, next_coupon, day_count
    )
    return coupon_payment * accrued_fraction
