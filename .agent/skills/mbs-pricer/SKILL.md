---
name: mbs-pricer
description: """ Use this skill to BUILD or EXTEND code that prices MBS Passthrough securities in the analytics engine. Triggers when a developer asks to add MBS support, implement CFY or PSA calculations, wire up a price_mbs() function, or handle bonds of type "MBS" in code. Also triggers when the task involves writing or modifying any code that computes accrued interest, CFY, WAL, or PSA for mortgage-backed securities, or when modifying output formatting to display MBS-specific columns. Do NOT use for standard bullet bonds (corporates, Treasuries, munis) — those use solve_ytm() in the existing analytics engine. """
--- 

# MBS Passthrough Pricer

## Agent Task

**Your job is to write and integrate code** that implements MBS passthrough pricing into the
existing `analytics_engine`. You are building functionality, not performing calculations yourself.

Specifically, you will:
1. Write the functions described in this skill as new Python modules/files
2. Integrate them into the existing codebase via the dispatch pattern shown below
3. Modify the output table to include MBS-specific columns when any MBS bond is present
4. Validate your implementation compiles and produces correct output against the benchmarks

Do **not** compute MBS prices or yields yourself in conversation — implement the code that does it.

---

## Scope

This skill covers building **cash flow yield (CFY) pricing only**. The following are explicitly
**out of scope** — do not attempt to implement them:

- **OAS (Option-Adjusted Spread)** — requires Monte Carlo or lattice interest rate models across many rate scenarios to value the embedded prepayment option. Do not approximate OAS from CFY spread to Treasury.
- **Duration/convexity under prepayment optionality** — effective duration requires the OAS framework.
- **Scenario analysis across rate paths** — CFY assumes a single static prepayment speed.

If the code is asked to return OAS by a caller, have it raise a `NotImplementedError` with a
clear message that OAS is out of scope, and return the CFY result instead.

---

## Input Contract

The model will receive **exactly these fields** for an MBS bond — no others should be assumed
or expected:

| Field | Type | Example | Notes |
|---|---|---|---|
| `bond_type` | str | `"MBS"` | Always "MBS" for this path |
| `coupon_rate` | float | `0.045` | Annual passthrough rate |
| `maturity` | float | `6.0` | **WAL in years**, not a calendar date |
| `clean_price` | float | `99.00` | Per $100 face |
| `settlement` | date | `2026-03-15` | Settlement date |
| `day_count` | str | `"ACT/360"` | Day count convention |
| `freq` | int | `12` | Payment frequency (monthly = 12) |

**Key constraints:**
- `maturity` holds the **WAL in years**, not a bullet maturity date. Treat it as `spec.wal`.
- `current_face` is always **100.0** — no pool factor will be provided.
- `seasoning` is always **0** — pools are assumed new.
- `term_months` is always **360** — pools are assumed 30-year.
- PSA speed is **never provided directly** — always solve for it from the WAL.

These defaults must be hardcoded in `price_mbs()`, not read from spec.

---

## Detection

Route to the MBS pricer when:
```python
spec.bond_type == "MBS"
```

---

## Output Table Format

The output table **always** includes **CFY (%)** and **PSA** columns. Non-MBS rows display `#`
in those columns. MBS bonds populate all columns including YTM.

Expected output with mixed bond types:

```
 Bond            | Accrued Interest | Dirty Price |    YTM (%) |    CFY (%) |     PSA
--------------------------------------------------------------------------------------
B1: UST          |           0.7212 |     98.9712 |    3.8119% |          # |       #
B2: IG Corp      |           0.0000 |    101.4000 |    4.8106% |          # |       #
B3: HY Corp      |           2.3111 |     94.4111 |   11.4601% |          # |       #
B4: MBS          |           0.1694 |     99.1694 |    4.6725% |    4.7160% |  274.71
B5: Zero Coupon  |           0.0000 |     95.0000 |    5.2632% |          # |       #
```

Rules:
- **YTM (%)** is populated for MBS rows by treating WAL as a bullet maturity (full principal
  returned at WAL date). This is an approximation — CFY BEY is the rigorous yield measure.
- **CFY (%)** and **PSA** show `#` for all non-MBS rows.
- CFY and PSA columns are **always present** — do not conditionally add or hide them.
- PSA formatted to 2 decimal places (e.g. `274.71`).
- CFY formatted as percentage to 4 decimal places (e.g. `4.7160%`).
- YTM formatted as percentage to 4 decimal places (e.g. `4.6725%`).

Detect MBS rows by checking `hasattr(result, 'mbs_details')` on each `BondResult`.

### MBS bond_type matching

Any bond whose `bond_type` contains the substring `"MBS"` (case-insensitive) should be routed
to `price_mbs()`. This covers values like `"MBS"`, `"MBS Passthrough"`, `"Agency MBS"`, etc:

```python
if "mbs" in spec.bond_type.lower():
    return price_mbs(spec)
return solve_ytm(spec)
```

---

## Key Concepts

### PSA Prepayment Model
- CPR ramps at `psa_speed × 0.2%` per month for months 1–30
- Plateaus at `psa_speed × 6%` from month 31 onwards
- 100 PSA = standard benchmark; ~275 PSA produces a WAL of 6 years on a new 30yr pool

```python
def get_cpr(month: int, psa_speed: float) -> float:
    if month <= 30:
        return psa_speed * 0.002 * month
    return psa_speed * 0.06

def cpr_to_smm(cpr: float) -> float:
    """Convert annual CPR to Single Monthly Mortality."""
    return 1 - (1 - cpr) ** (1 / 12)
```

### Accrued Interest
MBS accrue interest from the **1st of the settlement month**.

Example: settlement = March 15, 2026 → accrual start = March 1, 2026 (14 days accrued).

Use `day_count_fraction()` with `spec.day_count` — never hardcode the convention:

```python
from datetime import date
from analytics_engine.day_count import day_count_fraction

def mbs_accrued_interest(
    settlement: date,
    coupon_rate: float,
    day_count: str,
    current_face: float = 100.0,
) -> float:
    accrual_start = settlement.replace(day=1)
    dcf = day_count_fraction(accrual_start, settlement, day_count)
    return current_face * coupon_rate * dcf
```

---

## Cash Flow Generation

```python
def generate_mbs_cashflows(
    coupon_rate: float,
    psa_speed: float,
    term_months: int = 360,
    current_face: float = 100.0,
    seasoning_months: int = 0,
) -> list[dict]:
    """
    Generate monthly MBS cash flows under a PSA prepayment assumption.

    For the current input contract: term_months=360, current_face=100.0,
    seasoning_months=0 are always used — do not expose these as caller inputs.
    """
    balance = current_face
    monthly_rate = coupon_rate / 12
    cash_flows = []

    for i in range(1, term_months + 1):
        psa_month = i + seasoning_months
        cpr = get_cpr(psa_month, psa_speed)
        smm = cpr_to_smm(cpr)

        remaining_term = term_months - i + 1
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
```

---

## WAL Calculation

```python
def compute_wal(cash_flows: list[dict]) -> float:
    """Weighted Average Life in years."""
    total_principal = sum(cf["total_principal"] for cf in cash_flows)
    wal_months = sum(cf["t"] * cf["total_principal"] for cf in cash_flows) / total_principal
    return wal_months / 12
```

---

## Solving PSA from WAL

WAL is the only maturity input provided. Always solve for PSA from it — never assume a PSA speed:

```python
from scipy.optimize import brentq

def psa_from_wal(
    target_wal: float,
    coupon_rate: float,
    term_months: int = 360,
    current_face: float = 100.0,
    seasoning_months: int = 0,
) -> float:
    """
    Find the PSA speed that produces the given WAL.
    For a new 30yr 4.5% pool: WAL=6yr => ~275 PSA, WAL=10.94yr => 100 PSA.
    """
    def objective(psa):
        cfs = generate_mbs_cashflows(coupon_rate, psa, term_months, current_face, seasoning_months)
        return compute_wal(cfs) - target_wal

    return brentq(objective, 0.1, 30.0)
```

---

## CFY Solver

```python
def solve_cfy(cash_flows: list[dict], dirty_price: float) -> dict:
    """
    Solve for Cash Flow Yield.

    Returns:
        monthly_yield  - monthly IRR
        cfy_annual     - (1 + monthly)^12 - 1
        cfy_bey        - Bond Equivalent Yield: ((1+monthly)^6 - 1) * 2
                         Use BEY to compare with Treasuries / corporates.
    """
    from scipy.optimize import brentq

    def pv(y):
        return sum(cf["total_cf"] / (1 + y) ** cf["t"] for cf in cash_flows)

    monthly_yield = brentq(lambda y: pv(y) - dirty_price, 1e-6, 0.05)

    return {
        "monthly_yield": monthly_yield,
        "cfy_annual": (1 + monthly_yield) ** 12 - 1,
        "cfy_bey": ((1 + monthly_yield) ** 6 - 1) * 2,
    }
```

---

## Full Pricing Workflow

Implement in `analytics_engine/mbs.py`:

```python
from analytics_engine.models import BondResult, BondSpec

def price_mbs(spec: BondSpec) -> BondResult:
    """
    MBS passthrough pricing pipeline.

    Reads from spec:  bond_type, coupon_rate, maturity (=WAL in years),
                      clean_price, settlement, day_count, freq
    Assumes fixed:    current_face=100.0, term_months=360, seasoning=0
    PSA speed is solved internally from the WAL — it is never a spec input.
    """
    current_face = 100.0
    term_months  = 360
    seasoning    = 0
    wal          = spec.maturity   # maturity field carries WAL for MBS

    # Step 1: Solve PSA from WAL
    psa_speed = psa_from_wal(wal, spec.coupon_rate, term_months, current_face, seasoning)

    # Step 2: Accrued interest (from 1st of settlement month)
    accrued = mbs_accrued_interest(spec.settlement, spec.coupon_rate, spec.day_count, current_face)
    dirty_price = spec.clean_price + accrued

    # Step 3: Generate cash flows and compute WAL/CFY
    cash_flows = generate_mbs_cashflows(spec.coupon_rate, psa_speed, term_months, current_face, seasoning)
    wal_computed = compute_wal(cash_flows)
    cfy = solve_cfy(cash_flows, dirty_price)

    result = BondResult(
        spec=spec,
        accrued_interest=accrued,
        dirty_price=dirty_price,
        ytm=cfy["cfy_bey"],   # WAL treated as bullet maturity for YTM approximation; use cfy_bey for rigorous yield
    )
    result.mbs_details = {
        "psa_speed": psa_speed,
        "wal_years": wal_computed,
        "cfy_monthly": cfy["monthly_yield"],
        "cfy_annual": cfy["cfy_annual"],
        "cfy_bey": cfy["cfy_bey"],
        "num_cashflow_months": len(cash_flows),
    }
    return result
```

Note: `ytm=None` is set explicitly so the output formatter knows to leave the YTM column blank
for MBS rows and display CFY BEY in the dedicated CFY column instead.

---

## Dispatch Pattern

```python
def solve_bond(spec: BondSpec) -> BondResult:
    if "mbs" in spec.bond_type.lower():   # matches "MBS", "MBS Passthrough", "Agency MBS", etc.
        return price_mbs(spec)
    return solve_ytm(spec)   # existing corporate/treasury path
```

---

## Regression Benchmarks

Validate the implementation against these known-good values:

| Input | Expected Output |
|---|---|
| coupon=4.5%, clean=99.00, settle=2026-03-15, WAL=6yr, ACT/360 | PSA ~= 274.71, accrued ~= 0.1694, dirty ~= 99.1694, CFY BEY ~= 4.7160% |
| coupon=4.5%, dirty=99.1694, WAL=10.94yr (=> 100 PSA) | CFY BEY ~= 4.6506% |

---

## Caveats for MBS

| Topic | Note |
|---|---|
| **Accrual start** | Always the **1st of the settlement month** (e.g. settle=Mar 15 -> Mar 1). |
| **Day count** | Always use `spec.day_count` via `day_count_fraction()` — never hardcode. |
| **Fixed assumptions** | `current_face=100`, `term_months=360`, `seasoning=0` are hardcoded because the input contract never provides them. If the contract expands, these become spec fields. |
| **WAL as maturity** | `spec.maturity` carries the WAL for MBS — it is not a calendar date. |
| **YTM for MBS** | MBS `ytm` is set to CFY BEY, treating WAL as a bullet maturity. It is an approximation — the CFY column is the rigorous yield. Both are shown in the output table. |
| **OAS** | Out of scope — see Scope section above. |
