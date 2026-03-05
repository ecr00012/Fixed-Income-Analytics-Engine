# MBS Passthrough Pricer — Design

## Problem

The analytics engine currently handles bullet bonds (Treasuries, corporates, zero coupon)
via `solve_ytm()`. Bond B4 (MBS passthrough) is priced as a bullet approximation.
We need a proper MBS pricing pipeline that models prepayment behavior, generates
amortizing cash flows, and computes Cash Flow Yield (CFY).

## Design Decisions

1. **Model: separate `wal` field** — `BondSpec` keeps `maturity: date` for all bonds.
   A new `wal: float | None = None` field stores WAL in years for MBS. MBS bonds derive
   `maturity` as `settlement + wal years`. This lets MBS reuse the existing YTM solver
   for a bullet-equivalent approximation while also computing CFY.

2. **YTM reuse** — MBS calls `solve_ytm(spec)` to get bullet-equivalent YTM using the
   derived maturity date, then computes CFY separately. Both values appear in output.

3. **Single module** — All MBS logic lives in `analytics_engine/mbs.py`. The pipeline
   is cohesive (PSA → cashflows → CFY) and doesn't warrant splitting.

## Architecture

### Model Changes (`models.py`)

```python
@dataclass
class BondSpec:
    name: str
    clean_price: float
    coupon_rate: float
    maturity: date
    settlement: date
    freq: int
    day_count: str
    bond_type: str = ""
    wal: float | None = None

@dataclass
class BondResult:
    spec: BondSpec
    accrued_interest: float
    dirty_price: float
    ytm: float
    mbs_details: dict | None = None
```

### MBS Module (`mbs.py`)

| Function | Purpose |
|---|---|
| `get_cpr(month, psa_speed)` | CPR at a given month under PSA model (ramps 0.2%/mo to month 30, plateaus at 6×PSA) |
| `cpr_to_smm(cpr)` | Annual CPR → monthly prepayment rate: `1 - (1 - CPR)^(1/12)` |
| `generate_mbs_cashflows(coupon_rate, psa_speed)` | Monthly cash flows with scheduled + prepaid principal. Fixed: `term=360`, `face=100`, `seasoning=0` |
| `compute_wal(cash_flows)` | Principal-weighted average life in years |
| `psa_from_wal(target_wal, coupon_rate)` | Solve PSA speed producing target WAL via `scipy.optimize.brentq` |
| `mbs_accrued_interest(settlement, coupon_rate, day_count)` | Accrued from 1st of settlement month using `day_count_fraction()` |
| `solve_cfy(cash_flows, dirty_price)` | Monthly IRR → annual CFY → Bond Equivalent Yield |
| `price_mbs(spec)` | Orchestrator: solve PSA → accrued → cashflows → CFY → call `solve_ytm()` for YTM |

### Dispatch (`pricing.py`)

```python
def analyze_bond(spec: BondSpec) -> BondResult:
    if spec.bond_type and "mbs" in spec.bond_type.lower():
        return price_mbs(spec)
    return solve_ytm(spec)
```

### CLI Output (`cli.py`)

Always includes CFY (%) and PSA columns. Non-MBS rows show `#`:

```
 Bond            | Accrued Interest | Dirty Price |    YTM (%) |    CFY (%) |     PSA
--------------------------------------------------------------------------------------
B1: UST          |           0.7212 |     98.9712 |    3.8119% |          # |       #
B2: IG Corp      |           0.0000 |    101.4000 |    4.8106% |          # |       #
B3: HY Corp      |           2.3111 |     94.4111 |   11.4601% |          # |       #
B4: MBS          |           0.1694 |     99.1694 |    4.6725% |    4.7160% |  274.71
B5: Zero Coupon  |           0.0000 |     95.0000 |    5.2632% |          # |       #
```

### Dependencies

Add `scipy` to `pyproject.toml` for `brentq` root-finding.

## Testing

New file `tests/test_mbs.py`:
- PSA model: CPR ramp/plateau at months 1, 15, 30, 31
- `cpr_to_smm` conversion
- Cash flow generation: balance declines, all flows positive
- `compute_wal` against known values
- `psa_from_wal`: WAL=6yr → PSA ≈ 274.71
- Accrued interest: settle Mar 15 → 14 days → ≈ 0.1694
- `solve_cfy`: CFY BEY ≈ 4.7160%
- `price_mbs` integration: full pipeline matches benchmarks
- Existing 28 tests pass with no regressions

## Benchmarks

| Input | Expected |
|---|---|
| coupon=4.5%, clean=99.00, settle=2026-03-15, WAL=6yr, ACT/360 | PSA ≈ 274.71, accrued ≈ 0.1694, dirty ≈ 99.1694, CFY BEY ≈ 4.7160% |
| coupon=4.5%, dirty=99.1694, WAL=10.94yr (⇒ 100 PSA) | CFY BEY ≈ 4.6506% |

## Out of Scope

- OAS (requires Monte Carlo rate models)
- Duration/convexity under prepayment optionality
- Scenario analysis across rate paths
