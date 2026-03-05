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

