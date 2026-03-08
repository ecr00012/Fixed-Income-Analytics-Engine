from __future__ import annotations

from datetime import date

from scipy.optimize import brentq

from analytics_engine.day_count import day_count_fraction
from analytics_engine.models import BondResult, BondSpec
from analytics_engine.solver import solve_ytm


def get_cpr(month: int, psa_speed: float) -> float:
    """
    Purpose: Calculates the expected annualized Conditional Prepayment Rate (CPR) for 
    a specific month in the life of the mortgage pool using the PSA curve.

    Broader Application: The exact prepayment behavior of an MBS is technically unknown. 
    MBS pricers project future behavior by referencing standard industry curves.
    This function mathematically builds the PSA "ramp" (up to month 30) and "plateau" 
    (after month 30) to give us a dynamic annualized rate to use for any given future month.
    """
    if month <= 30:
        return psa_speed * 0.002 * month
    return psa_speed * 0.06


def cpr_to_smm(cpr: float) -> float:
    """
    Purpose: Converts the annualized CPR into a Single Monthly Mortality (SMM) rate.

    Broader Application: Because mortgages (and therefore MBS passthroughs) pay out on a
    monthly basis, we cannot use an annualized prepayment rate directly to calculate a 
    given month's cash flow. The engine needs to de-annualize the CPR into SMM to determine 
    xactly what percentage of the remaining principal is prepaid this specific month.
    """
    cpr = min(cpr, 1.0)  
    return 1 - (1 - cpr) ** (1 / 12)


def generate_mbs_cashflows(
    coupon_rate: float,
    psa_speed: float,
    term_months: int = 360,
    current_face: float = 100.0,
    seasoning_months: int = 0,
) -> list[dict]:
    """
    Purpose: Simulates the entire lifespan of the MBS month-by-month, projecting what the scheduled 
    interest, scheduled principal, and unscheduled principal (prepayment) will be for each period 
    until the face value is $0.

    Broader Application: This is the core engine for modeling MBS cash flow projections. Unlike standard 
    physical bonds which have highly predictable fixed coupons and a massive bullet principal 
    payment at the end, an MBS's principal amortizes over time and changes based on prepayments. You 
    need this complete simulated schedule to dynamically solve for the yield, average life, 
    or value of the bond.
    """
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
    """
    Purpose: Iterates over the generated cash flow schedule to calculate the 
    Weighted Average Life (WAL) in years.

    Broader Application: MBS securities do not typically last their full stated term length 
    (e.g., 30 years) because homeowners move or refinance, prepaying their mortgages. 
    Since the actual maturity date is variable, investors price and quote an MBS based on its WAL.
    """
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
    """
    Purpose: Finds the specific PSA prepayment speed that causes the MBS to pay off 
    in exactly the target number of years (WAL). 

    Broader Application: Since the WAL is the primary driver of an MBS's price and yield, 
    this function is essential for "reverse engineering" the market's prepayment expectations. 
    If a 5-year WAL is bid in the market, this function tells you what PSA speed that implies.
    """
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
    """
    Purpose: Calculates the accrued interest on the MBS from the first day of the settlement month 
    up to the settlement date.

    Broader Application: Accrued interest is the portion of the next coupon payment that belongs 
    to the seller for the days they owned the bond during the coupon period. 
    Since MBS coupons are paid monthly (unlike standard bonds which are often semi-annual), 
    this calculation is straightforward but critical for ensuring the buyer pays the seller the 
    correct amount for the "old" principal that is being transferred.
    """
    accrual_start = settlement.replace(day=1)
    dcf = day_count_fraction(accrual_start, settlement, day_count)
    return current_face * coupon_rate * dcf


def solve_cfy(cash_flows: list[dict], dirty_price: float) -> dict:
    """
    Purpose: Calculates the internal rate of return—the Cash Flow Yield (CFY)—
    that makes the present discounted value of all projected monthly cash flows 
    equal to the bond's dirty price (clean market price + accrued interest).

    Broader Application: Since MBS cash flows are wildly non-standard, you cannot use standard yield formulas. 
    This solver provides three perspectives on the yield: the raw monthly yield, the standard annualized CFY, 
    and the Bond Equivalent Yield (BEY) so the trader can compare this MBS "Bond 4" head-to-head with semi-annual 
    paying Treasury bonds.
    """
    def pv(y):
        return sum(cf["total_cf"] / (1 + y) ** cf["t"] for cf in cash_flows)

    monthly_yield = brentq(lambda y: pv(y) - dirty_price, 1e-6, 0.05)

    return {
        "monthly_yield": monthly_yield,
        "cfy_annual": (1 + monthly_yield) ** 12 - 1,
        "cfy_bey": ((1 + monthly_yield) ** 6 - 1) * 2,
    }


def price_mbs(spec: BondSpec) -> BondResult:
    """
    Purpose: Acts as the primary orchestrator/pipeline. 
    It extracts requirements from the BondSpec object, wires all the previous independent functions together 
    in order, and wraps the calculations into a standardized BondResult output format.
    
    Broader Application: This is the entry point for the analytics engine to consume MBS requests. 
    It normalizes MBS processing so that the broader application can accept standard bonds or MBS bonds seamlessly. 
    It sequentially extracts the exact PSA speed based on market-quoted WAL, generates the actual expected lifetime cash flows, 
    prices those cash flows out, and returns a rich set of metrics (YTM, WAL, CFY, CPR, etc.) to the user.
    """
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


