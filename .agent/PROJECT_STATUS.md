# Project Status
**Last Updated:** 2026-03-08  
**Status:** ✅ Feature Complete — All 52 tests passing

---

## Overview

This project implements a **Fixed Income Analytics Engine** for a portfolio management system. The engine prices and computes key bond analytics (accrued interest, dirty price, YTM, CFY) for a portfolio of five bonds spanning asset classes: US Treasuries, IG Corporate, HY Corporate, MBS Passthrough, and Zero-Coupon.

The core solver is a **Hybrid Newton-Raphson × Bisection** algorithm. The MBS pricer adds a full **PSA prepayment model** and **Cash Flow Yield (CFY)** calculation on top.

---

## Current Analytics Output

| Bond            | Accrued Interest | Dirty Price | YTM (%)  | CFY (BEY) | PSA Speed |
|:----------------|:----------------:|:-----------:|:--------:|:---------:|:---------:|
| B1: UST         | 0.7212           | 98.9712     | 3.8119%  | —         | —         |
| B2: IG Corp     | 0.0000           | 101.4000    | 4.8106%  | —         | —         |
| B3: HY Corp     | 2.3111           | 94.4111     | 11.4601% | —         | —         |
| B4: MBS         | 0.1750           | 99.1750     | 4.6225%  | 4.7148%   | 274.71%   |
| B5: Zero Coupon | 0.0000           | 95.0000     | 5.2632%  | —         | —         |

---

## Architecture

```
analytics_engine/
├── models.py        — BondSpec and BondResult dataclasses
├── day_count.py     — ACT/ACT, 30/360, ACT/360 conventions
├── cash_flows.py    — Coupon schedule generation & accrued interest
├── solver.py        — Hybrid Newton-Raphson × Bisection YTM solver
├── mbs.py           — PSA model, WAL, CFY, and MBS pricing pipeline
├── pricing.py       — Portfolio dispatcher (routes MBS vs. standard bonds)
└── cli.py           — Command-line runner with formatted output table
```

### Key Design Decisions

- **Modular separation**: Cash flow generation, day count conventions, root solving, and MBS math are fully decoupled modules.
- **Generic dispatch**: `pricing.py::analyze_bond()` routes any bond to the correct pricer based on `bond_type` field, making it trivial to add new asset classes.
- **Hybrid solver**: Newton-Raphson is attempted first each iteration (fast convergence); Bisection is used as a fallback when the Newton step escapes the bracket (guaranteed convergence). Bracket: `[-5%, 200%]`.
- **Zero-coupon fast path**: ZCBs bypass iteration entirely — solved via closed-form `(100/dirty_price)^(1/t) - 1`.
- **MBS pipeline**: WAL → PSA speed (via `brentq`), PSA → monthly cash flows → CFY (via `brentq`), + bullet-equivalent YTM via standard solver.

---

## Test Coverage

| Test File            | Classes / Tests | Coverage Area                                  |
|:---------------------|:---------------:|:-----------------------------------------------|
| `test_day_count.py`  | 4 / 8           | ACT/ACT (leap/non-leap), 30/360, ACT/360, errors |
| `test_cash_flows.py` | 2 / 6           | Coupon schedules, accrued interest edge cases    |
| `test_models.py`     | — / 5           | BondSpec / BondResult dataclass construction     |
| `test_solver.py`     | 2 / 8           | `price_from_yield`, YTM convergence (all bonds)  |
| `test_pricing.py`    | 2 / 5           | Portfolio dispatch, MBS routing                  |
| `test_mbs.py`        | 5 / 20          | PSA model, SMM, cash flows, WAL, CFY, full pipeline |
| **Total**            | **— / 52**      | **52 / 52 passing ✅**                          |

Run tests with:
```bash
uv run python -m pytest tests/ -v
```

---

## Key Assumptions & Modeling Notes

### Accrued Interest
- **Corporate bonds (B2, B3)**: Previous coupon date is assumed to be exactly one period prior to maturity, on the same calendar day (backward from maturity convention).
- **MBS (B4)**: Accrued interest calculated from the **first of the settlement month** (March 1, 2026) to settlement (March 15, 2026) — 14 days — per Fannie Mae/Freddie Mac market convention.

### MBS Pricing (B4)
- **WAL as bullet maturity**: The 6-year WAL is treated as a bullet maturity for computing a comparable YTM alongside the CFY.
- **PSA speed**: Solved via root-finding (`brentq`) over `[0.1, 30.0]` PSA to hit the target 6-year WAL. Result: **~2.7471× (274.71% PSA)**.
- **CFY reported as BEY**: `((1 + monthly_yield)^6 - 1) × 2` for comparability with semiannual Treasury yields.
- **No seasoning assumed**: Pool treated as new (month 1 of PSA ramp).

### YTM Solver Bracket
- Initial bracket: `[-0.05, 2.0]` (−5% to 200%) covers all realistic fixed income yield scenarios including deeply distressed bonds.

---

## Documentation

| Document | Path | Description |
|:---------|:-----|:------------|
| YTM Solver Design Plan | `docs/plans/2026-03-04-ytm-solver-design.md` | Original solver architecture and algorithm design |
| MBS Pricer Design | `docs/plans/2026-03-05-mbs-pricer-design.md` | MBS PSA + CFY design |
| MBS Pricer Implementation | `docs/plans/2026-03-05-mbs-pricer-implementation.md` | Full MBS implementation walkthrough |
| YTM Solver Walkthrough | `docs/walkthroughs/2026-03-04-ytm-solver-walkthrough.md` | Post-implementation YTM solver proof |
| Solver Deep Dive | `docs/walkthroughs/2026-03-07-solver-deep-dive.md` | Detailed solver interval / bracketing explanation |
| Bond 4 Deep Dive | `docs/walkthroughs/bond4_deep_dive.md` | MBS-specific analysis and assumptions |

---

## Environment

- **Runtime**: Python 3.11 via `uv`
- **Dependencies**: `pytest`, `scipy`, `python-dateutil`
- **Setup**: `uv sync`
- **Run CLI**: `uv run python -m analytics_engine`

---

## Potential Future Work

- [ ] Add spread-based analytics (OAS, Z-spread, G-spread)
- [ ] Extend CLI to accept bond input from a JSON/CSV file
- [ ] Add duration and convexity calculations (modified/Macaulay)
- [ ] Support for floating-rate bonds (FRNs)
