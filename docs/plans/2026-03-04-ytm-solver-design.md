# Fixed Income Analytics Engine — YTM Solver Design

## Problem Statement

Build a Yield-to-Maturity solver using a hybrid Newton-Raphson + Bisection root-finding method. The engine must compute accrued interest, dirty price, and YTM for five bonds spanning different types (UST, IG Corp, HY Corp, MBS passthrough, zero coupon), day count conventions (ACT/ACT, 30/360, ACT/360), and coupon frequencies (1, 2, 12).

## Architecture: Layered Modules by Responsibility

```
analytics_engine/
├── __init__.py
├── models.py          # Bond dataclass, result dataclass
├── day_count.py       # ACT/ACT, 30/360, ACT/360 conventions
├── cash_flows.py      # Coupon schedule generation, accrued interest
├── solver.py          # Hybrid Newton-Raphson + bisection root-finder
├── pricing.py         # Orchestrates: dirty price, YTM solve
├── cli.py             # Pretty-print table runner

tests/
├── test_day_count.py
├── test_cash_flows.py
├── test_solver.py
├── test_pricing.py
```

Each module maps to one responsibility from the spec. The coupon schedule is generated internally for intermediate calculation but is not surfaced as a deliverable.

---

## Module Design

### 1. `models.py` — Data Types

Two dataclasses with clean separation of input and output:

```python
@dataclass
class BondSpec:
    name: str                    # e.g. "B1: UST"
    clean_price: float           # quoted price excluding accrued interest
    coupon_rate: float           # annual rate, e.g. 0.035 for 3.5%
    maturity: date               # maturity date
    settlement: date             # settlement date
    freq: int                    # coupons per year (1, 2, 12)
    day_count: str               # "ACT/ACT", "30/360", "ACT/360"

@dataclass
class BondResult:
    spec: BondSpec
    accrued_interest: float
    dirty_price: float
    ytm: float                   # annualized yield-to-maturity
```

### 2. `day_count.py` — Day Count Conventions

Three pure functions plus a dispatcher:

- **`day_count_fraction(start, end, convention)`** — routes to the correct convention
- **`act_act(start, end)`** — actual days / actual days in year (handles leap years)
- **`thirty_360(start, end)`** — 30/360 convention (months = 30 days, year = 360)
- **`act_360(start, end)`** — actual days / 360

All are pure functions: dates in, float out. Extensible via dispatcher pattern.

### 3. `cash_flows.py` — Cash Flow Generation

Two functions used internally by the solver:

- **`generate_coupon_schedule(settlement, maturity, freq)`** — generates remaining coupon dates from settlement to maturity using backward generation from maturity (standard bond convention). Handles all frequencies uniformly.

- **`compute_accrued_interest(settlement, coupon_rate, freq, day_count, prev_coupon_date, next_coupon_date)`** — computes accrued interest as the pro-rata share of the current coupon period:
  ```
  accrued = (coupon_rate / freq) * day_count_fraction(prev_coupon, settlement)
            / day_count_fraction(prev_coupon, next_coupon)
  ```
  Returns 0 for zero-coupon bonds.

The coupon schedule is intermediate data — it is consumed by the solver and accrued interest computation but not surfaced in the output.

### 4. `solver.py` — Hybrid Newton-Raphson + Bisection

The core algorithm:

- **`price_from_yield(ytm, coupon_rate, settlement, maturity, freq, day_count)`** — computes present value of all future cash flows at a given yield. Also returns the derivative (dPrice/dYield) needed by Newton-Raphson.

- **`solve_ytm(clean_price, coupon_rate, maturity, settlement, freq, day_count)`** — the main entry point:
  1. Compute accrued interest and dirty price
  2. Find an initial bracket `[a, b]` where the price function straddles the target dirty price
  3. Hybrid iteration loop:
     - Compute Newton-Raphson step using the derivative
     - **If** Newton step stays inside bracket and reduces error → accept it
     - **Else** → bisection step (midpoint of bracket)
     - Update bracket bounds
     - Convergence: tolerance ~1e-10, max ~100 iterations
  4. Return `BondResult`

- **Zero-coupon short-circuit**: For zero-coupon bonds (B5), use closed-form:
  `YTM = (face / price) ^ (1/T) - 1`

### 5. `pricing.py` — Orchestration

Thin public API layer:

- **`analyze_bond(spec: BondSpec) -> BondResult`** — takes a `BondSpec`, orchestrates the computation pipeline, returns a `BondResult`.
- **`analyze_portfolio(specs: list[BondSpec]) -> list[BondResult]`** — convenience wrapper over a list.

### 6. `cli.py` — Runner

- Defines 5 bond specs (B1–B5) as data
- Calls `analyze_portfolio`
- Pretty-prints results as a formatted table
- Entry point: `uv run python -m analytics_engine.cli`

---

## Target Bonds

| Bond | Type         | Coupon | Maturity   | Clean Price | Day Count | Freq |
|------|------------- |--------|------------|-------------|-----------|------|
| B1   | UST          | 3.5%   | 2032-06-30 | 98.25       | ACT/ACT   | 2    |
| B2   | IG Corp      | 5.25%  | 2029-09-15 | 101.40      | 30/360    | 2    |
| B3   | HY Corp      | 8.0%   | 2028-12-01 | 92.10       | 30/360    | 2    |
| B4   | MBS          | 4.5%   | 2032-03-15 | 99.00       | ACT/360   | 12   |
| B5   | Zero Coupon  | 0%     | 2027-03-15 | 95.00       | ACT/ACT   | 1    |

All bonds settle on 2026-03-15. B4 maturity is settlement + 6 years (WAL assumption).

---

## Testing Strategy (Full TDD)

Tests are written **before** implementation using `pytest`.

| Test File             | Covers                                                    |
|-----------------------|-----------------------------------------------------------|
| `test_day_count.py`   | Known date pairs → expected year fractions per convention |
| `test_cash_flows.py`  | Known bonds → expected accrued interest, schedule counts  |
| `test_solver.py`      | Known bonds → expected YTM values                        |
| `test_pricing.py`     | Integration: full BondSpec → BondResult for all 5 bonds  |

**Running tests**: `uv run python -m pytest tests/ -v`

---

## Decisions Log

| Decision                          | Rationale                                                      |
|-----------------------------------|----------------------------------------------------------------|
| Layered modules (Approach B)      | Spec requires separable cash flow, accrual, and root solving   |
| Numerical packages allowed        | User preference; keeps focus on algorithm, not plumbing        |
| Newton-Raphson primary            | Spec requirement; bisection is the fallback for safety         |
| Zero-coupon closed-form           | No iteration needed; exact solution available                  |
| Coupon schedule is internal only  | Not a deliverable; used for intermediate pricing calculations  |
| Full TDD                          | User preference; tests written before implementation           |
