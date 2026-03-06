from datetime import date

from dateutil.relativedelta import relativedelta

from analytics_engine.cash_flows import compute_accrued_interest, generate_coupon_schedule
from analytics_engine.day_count import day_count_fraction
from analytics_engine.models import BondResult, BondSpec


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


def _find_prev_coupon(settlement: date, maturity: date, freq: int) -> date:
    """Find the most recent coupon date at or before settlement.
    To calculate interest accrued it can be assumed that the previous coupon date is uniform with the maturity date.
    i.e. For Bond 3, following a semiannual schedule, the last coupon date was 12/01/25.

    Assumptions: B4 — MBS Passthrough: Accrued interest calculated using ACT/360 
    from an assumed prior coupon date of February March 1, 2026 (14 days). 
    YTM computed as monthly IRR × 12 (nominal bond-equivalent yield) treating the 6-year WAL as a bullet maturity. 
    No prepayment model applied; principal assumed to return in full at WAL.
    WAL of 6 years treated as bullet maturity for pricing purposes. 
    A full treatment would require a scheduled amortization model and PSA prepayment assumption, 
    which cannot be derived from the given inputs.
    
"""
    months_per_period = 12 // freq
    current = maturity
    while current > settlement:
        current -= relativedelta(months=months_per_period)
    return current


def solve_ytm(
    spec: BondSpec,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> BondResult:
    """
    Solve for YTM using a hybrid Newton-Raphson + Bisection method.

    Algorithm:
    1. Find a bracketing interval [a, b] where the pricing function straddles dirty price.
    2. In each iteration, attempt a Newton-Raphson step.
    3. If the Newton step stays inside [a, b] → accept it (fast convergence).
    4. Otherwise → fall back to bisection (guaranteed convergence).
    5. Zero-coupon bonds use the closed-form solution directly.

    Returns BondResult with accrued_interest, dirty_price, and ytm.
    """
    # Step 1: Compute accrued interest
    if spec.freq == 0 or spec.coupon_rate == 0.0:
        accrued = 0.0
    else:
        schedule = generate_coupon_schedule(spec.settlement, spec.maturity, spec.freq)
        prev_coupon = _find_prev_coupon(spec.settlement, spec.maturity, spec.freq)
        next_coupon = schedule[0]
        accrued = compute_accrued_interest(
            spec.settlement,
            spec.coupon_rate,
            spec.freq,
            spec.day_count,
            prev_coupon,
            next_coupon,
        )

    dirty_price = spec.clean_price + accrued

    # Step 2: Zero-coupon — use closed-form solution
    if spec.freq == 0 or spec.coupon_rate == 0.0:
        t = day_count_fraction(spec.settlement, spec.maturity, spec.day_count)
        ytm = (100.0 / dirty_price) ** (1.0 / t) - 1.0
        return BondResult(spec=spec, accrued_interest=accrued, dirty_price=dirty_price, ytm=ytm)

    # Step 3: Find initial bracket [a, b]
    a, b = -0.05, 2.0
    fa = (
        price_from_yield(a, spec.coupon_rate, spec.settlement, spec.maturity, spec.freq, spec.day_count)[0]
        - dirty_price
    )
    fb = (
        price_from_yield(b, spec.coupon_rate, spec.settlement, spec.maturity, spec.freq, spec.day_count)[0]
        - dirty_price
    )

    if fa * fb > 0:
        raise ValueError(f"Cannot bracket YTM for {spec.name!r}: check bond inputs")

    # Start with midpoint as initial guess
    x = (a + b) / 2.0

    # Step 4: Hybrid iteration
    for _ in range(max_iter):
        px, dpx = price_from_yield(
            x, spec.coupon_rate, spec.settlement, spec.maturity, spec.freq, spec.day_count
        )
        fx = px - dirty_price

        if abs(fx) < tol:
            return BondResult(spec=spec, accrued_interest=accrued, dirty_price=dirty_price, ytm=x)

        # Attempt Newton-Raphson step
        if dpx != 0:
            x_newton = x - fx / dpx
        else:
            x_newton = None

        # Accept Newton step only if it stays inside the bracket
        if x_newton is not None and a < x_newton < b:
            x_next = x_newton
        else:
            # Fallback: bisection
            x_next = (a + b) / 2.0

        # Update bracket
        px_next = price_from_yield(
            x_next, spec.coupon_rate, spec.settlement, spec.maturity, spec.freq, spec.day_count
        )[0]
        fx_next = px_next - dirty_price

        if fa * fx_next < 0:
            b = x_next
            fb = fx_next
        else:
            a = x_next
            fa = fx_next

        x = x_next

    raise ValueError(
        f"YTM solver did not converge for {spec.name!r} after {max_iter} iterations"
    )
