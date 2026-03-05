# Fixed Income Analytics Engine — Implementation Walkthrough

## What Was Built

A Yield-to-Maturity (YTM) solver using a hybrid Newton-Raphson + Bisection method, structured as layered Python modules.

## Module Structure

```
analytics_engine/
├── models.py      # BondSpec, BondResult dataclasses
├── day_count.py   # ACT/ACT, 30/360, ACT/360 conventions
├── cash_flows.py  # Coupon schedule generation, accrued interest
├── solver.py      # price_from_yield + hybrid N-R/bisection solve_ytm
├── pricing.py     # Public API: analyze_bond, analyze_portfolio
├── cli.py         # Formatted table output
└── __main__.py    # Entry point: python -m analytics_engine
```

## Tests: 28/28 Passing

```
uv run python -m pytest tests/ -v
```

| Test File             | Tests | Coverage                                              |
|-----------------------|-------|-------------------------------------------------------|
| `test_models.py`      | 2     | BondSpec and BondResult dataclass creation             |
| `test_day_count.py`   | 8     | ACT/ACT (leap/non-leap), 30/360, ACT/360, error handling |
| `test_cash_flows.py`  | 6     | Coupon schedules (semi, monthly, zero), accrued interest |
| `test_solver.py`      | 8     | price_from_yield, par/discount/premium bonds, zero coupon, convergence |
| `test_pricing.py`     | 4     | analyze_bond, dirty price identity, portfolio of 5 bonds |

## CLI Output

```
uv run python -m analytics_engine

Bond                 |   Accrued Interest |   Dirty Price |    YTM (%)
----------------------------------------------------------------------
B1: UST              |             0.7212 |       98.9712 |    3.8119%
B2: IG Corp          |             0.0000 |      101.4000 |    4.8106%
B3: HY Corp          |             2.3111 |       94.4111 |   11.4601%
B4: MBS              |             0.0000 |       99.0000 |    4.6225%
B5: Zero Coupon      |             0.0000 |       95.0000 |    5.2632%
```

## Sanity Checks

| Check | Observed | Expected |
|-------|----------|----------|
| B1 (UST at discount) → YTM > coupon rate | 3.81% > 3.5% ✅ | ✅ |
| B2 (IG Corp at premium) → YTM < coupon rate | 4.81% < 5.25% ✅ | ✅ |
| B3 (HY Corp at discount) → YTM > coupon rate | 11.46% > 8.0% ✅ | ✅ |
| B5 (Zero coupon) → accrued = 0 | 0.0000 ✅ | ✅ |
| B5 closed-form: (100/95)^1 - 1 ≈ 5.263% | 5.2632% ✅ | ✅ |

## Git History

```
e1f1358 feat: add CLI runner with pretty-print table output
06db7dd feat: add pricing orchestration layer
48b43a6 feat: add hybrid Newton-Raphson + bisection YTM solver
0097e6d feat: add price_from_yield with derivative for Newton-Raphson
0c4dc6a feat: add coupon schedule generation and accrued interest
b8800bf feat: add day count conventions (ACT/ACT, 30/360, ACT/360)
14ff7a6 feat: add BondSpec and BondResult dataclasses with tests
```
