from __future__ import annotations

from datetime import date

from scipy.optimize import brentq

from analytics_engine.day_count import day_count_fraction


def get_cpr(month: int, psa_speed: float) -> float:
    """CPR under PSA model. Ramps 0.2%/mo for months 1-30, plateaus after."""
    if month <= 30:
        return psa_speed * 0.002 * month
    return psa_speed * 0.06


def cpr_to_smm(cpr: float) -> float:
    """Convert annual CPR to Single Monthly Mortality."""
    cpr = min(cpr, 1.0)  # clamp: CPR > 100% is nonsensical
    return 1 - (1 - cpr) ** (1 / 12)


def generate_mbs_cashflows(
    coupon_rate: float,
    psa_speed: float,
    term_months: int = 360,
    current_face: float = 100.0,
    seasoning_months: int = 0,
) -> list[dict]:
    """Generate monthly MBS cash flows under a PSA prepayment assumption."""
    balance = current_face
    monthly_rate = coupon_rate / 12
    cash_flows = []

    for i in range(1, term_months + 1):
        psa_month = i + seasoning_months
        cpr = get_cpr(psa_month, psa_speed)
        smm = cpr_to_smm(cpr)

        remaining_term = term_months - i + 1
        if balance < 1e-6:
            break
        scheduled_payment = balance * monthly_rate / (
            1 - (1 + monthly_rate) ** (-remaining_term)
        )
        scheduled_interest = balance * monthly_rate
        scheduled_principal = scheduled_payment - scheduled_interest
        prepayment = (balance - scheduled_principal) * smm

        total_principal = scheduled_principal + prepayment
        total_cf = scheduled_interest + total_principal

        cash_flows.append({
            "t": i,
            "balance_bop": balance,
            "interest": scheduled_interest,
            "sched_principal": scheduled_principal,
            "prepayment": prepayment,
            "total_principal": total_principal,
            "total_cf": total_cf,
        })

        balance -= total_principal
        if balance < 1e-6:
            break

    return cash_flows


def compute_wal(cash_flows: list[dict]) -> float:
    """Weighted Average Life in years."""
    total_principal = sum(cf["total_principal"] for cf in cash_flows)
    wal_months = sum(cf["t"] * cf["total_principal"] for cf in cash_flows) / total_principal
    return wal_months / 12


def psa_from_wal(
    target_wal: float,
    coupon_rate: float,
    term_months: int = 360,
    current_face: float = 100.0,
    seasoning_months: int = 0,
) -> float:
    """Find the PSA speed that produces the given WAL."""
    def objective(psa):
        cfs = generate_mbs_cashflows(coupon_rate, psa, term_months, current_face, seasoning_months)
        return compute_wal(cfs) - target_wal

    return brentq(objective, 0.1, 30.0)


def mbs_accrued_interest(
    settlement: date,
    coupon_rate: float,
    day_count: str,
    current_face: float = 100.0,
) -> float:
    """Accrued interest from 1st of settlement month."""
    accrual_start = settlement.replace(day=1)
    dcf = day_count_fraction(accrual_start, settlement, day_count)
    return current_face * coupon_rate * dcf


def solve_cfy(cash_flows: list[dict], dirty_price: float) -> dict:
    """Solve for Cash Flow Yield. Returns monthly, annual, and BEY."""
    def pv(y):
        return sum(cf["total_cf"] / (1 + y) ** cf["t"] for cf in cash_flows)

    monthly_yield = brentq(lambda y: pv(y) - dirty_price, 1e-6, 0.05)

    return {
        "monthly_yield": monthly_yield,
        "cfy_annual": (1 + monthly_yield) ** 12 - 1,
        "cfy_bey": ((1 + monthly_yield) ** 6 - 1) * 2,
    }


def price_mbs(spec: "BondSpec") -> "BondResult":
    """MBS passthrough pricing pipeline.

    Reads from spec: bond_type, coupon_rate, maturity (date), wal (float years),
                     clean_price, settlement, day_count, freq
    Assumes fixed: current_face=100.0, term_months=360, seasoning=0
    PSA speed is solved internally from the WAL.
    """
    from analytics_engine.models import BondResult, BondSpec
    from analytics_engine.solver import solve_ytm

    current_face = 100.0
    term_months = 360
    seasoning = 0
    wal = spec.wal

    # Step 1: Solve PSA from WAL
    psa_speed = psa_from_wal(wal, spec.coupon_rate, term_months, current_face, seasoning)

    # Step 2: Accrued interest (from 1st of settlement month)
    accrued = mbs_accrued_interest(spec.settlement, spec.coupon_rate, spec.day_count, current_face)
    dirty_price = spec.clean_price + accrued

    # Step 3: Cash flows and CFY
    cash_flows = generate_mbs_cashflows(spec.coupon_rate, psa_speed, term_months, current_face, seasoning)
    wal_computed = compute_wal(cash_flows)
    cfy = solve_cfy(cash_flows, dirty_price)

    # Step 4: Bullet-equivalent YTM via existing solver
    ytm_result = solve_ytm(spec)

    return BondResult(
        spec=spec,
        accrued_interest=accrued,
        dirty_price=dirty_price,
        ytm=ytm_result.ytm,
        mbs_details={
            "psa_speed": psa_speed,
            "wal_years": wal_computed,
            "cfy_monthly": cfy["monthly_yield"],
            "cfy_annual": cfy["cfy_annual"],
            "cfy_bey": cfy["cfy_bey"],
            "num_cashflow_months": len(cash_flows),
        },
    )


