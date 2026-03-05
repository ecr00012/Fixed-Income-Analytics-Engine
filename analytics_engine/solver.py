from datetime import date

from analytics_engine.cash_flows import generate_coupon_schedule
from analytics_engine.day_count import day_count_fraction


def price_from_yield(
    ytm: float,
    coupon_rate: float,
    settlement: date,
    maturity: date,
    freq: int,
    day_count: str,
) -> tuple[float, float]:
    """
    Compute the dirty price of a bond and its derivative dPrice/dYTM given a yield.

    Returns:
        (price, dpdy): dirty price and its derivative with respect to YTM.
    """
    schedule = generate_coupon_schedule(settlement, maturity, freq)
    coupon = coupon_rate / freq * 100  # coupon per period, per 100 face value
    period_yield = ytm / freq

    price = 0.0
    dpdy = 0.0

    for coupon_date in schedule:
        # Time in periods from settlement to this cash flow date
        t = day_count_fraction(settlement, coupon_date, day_count) * freq
        cf = coupon
        if coupon_date == maturity:
            cf += 100  # principal repaid at maturity

        discount = (1 + period_yield) ** t
        price += cf / discount
        # Derivative: d/d(ytm) [ cf / (1 + ytm/freq)^t ] = -t * cf / ((1 + ytm/freq)^(t+1) * freq)
        dpdy += -t * cf / (discount * (1 + period_yield) * freq)

    return price, dpdy
