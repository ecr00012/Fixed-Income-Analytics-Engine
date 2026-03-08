# MBS Passthrough Pricer Implementation Plan

**Goal:** Add MBS passthrough pricing (PSA prepayment model, CFY solver) to the analytics engine.

**Architecture:** Single new module `analytics_engine/mbs.py` contains all MBS logic. `BondSpec` gains `bond_type` and `wal` fields. Dispatch in `pricing.py` routes MBS bonds to `price_mbs()`, which computes CFY and reuses `solve_ytm()` for bullet-equivalent YTM. CLI output always shows CFY/PSA columns.

**Tech Stack:** Python 3.11, scipy (brentq), pytest

---

### Task 1: Add `scipy` Dependency

**Files:**
- Modify: `pyproject.toml:7-9`

**Step 1: Add scipy to dependencies**

```toml
dependencies = [
    "python-dateutil>=2.9.0.post0",
    "scipy>=1.11.0",
]
```

**Step 2: Sync environment**

Run: `uv sync`
Expected: scipy installed successfully

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add scipy dependency for MBS solver"
```

---

### Task 2: Update `BondSpec` and `BondResult` Models

**Files:**
- Modify: `analytics_engine/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing tests**

Add to `tests/test_models.py`:

```python
def test_bond_spec_has_bond_type_default():
    spec = BondSpec(
        name="Test", clean_price=100.0, coupon_rate=0.05,
        maturity=date(2030, 1, 1), settlement=date(2026, 1, 1),
        freq=2, day_count="30/360",
    )
    assert spec.bond_type == ""
    assert spec.wal is None


def test_bond_spec_with_mbs_fields():
    spec = BondSpec(
        name="MBS", clean_price=99.0, coupon_rate=0.045,
        maturity=date(2032, 3, 15), settlement=date(2026, 3, 15),
        freq=12, day_count="ACT/360",
        bond_type="MBS", wal=6.0,
    )
    assert spec.bond_type == "MBS"
    assert spec.wal == 6.0


def test_bond_result_mbs_details_default():
    spec = BondSpec(
        name="Test", clean_price=100.0, coupon_rate=0.05,
        maturity=date(2030, 1, 1), settlement=date(2026, 1, 1),
        freq=2, day_count="30/360",
    )
    result = BondResult(spec=spec, accrued_interest=0.0, dirty_price=100.0, ytm=0.05)
    assert result.mbs_details is None
```

**Step 2: Run tests to verify they fail**

Run: `uv run python -m pytest tests/test_models.py -v`
Expected: FAIL — `bond_type`, `wal`, `mbs_details` not defined

**Step 3: Update models.py**

```python
from dataclasses import dataclass, field
from datetime import date


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

**Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_models.py -v`
Expected: ALL PASS

**Step 5: Run full suite to verify no regressions**

Run: `uv run python -m pytest -v`
Expected: All 28 existing tests PASS

**Step 6: Commit**

```bash
git add analytics_engine/models.py tests/test_models.py
git commit -m "feat: add bond_type, wal, mbs_details fields to models"
```

---

### Task 3: PSA Prepayment Model Functions

**Files:**
- Create: `analytics_engine/mbs.py`
- Create: `tests/test_mbs.py`

**Step 1: Write the failing tests**

Create `tests/test_mbs.py`:

```python
import pytest
from analytics_engine.mbs import get_cpr, cpr_to_smm


class TestPSAModel:
    def test_cpr_month_1(self):
        # 100 PSA: month 1 → 1.0 * 0.002 * 1 = 0.002
        assert abs(get_cpr(1, 1.0) - 0.002) < 1e-10

    def test_cpr_month_15(self):
        # 100 PSA: month 15 → 1.0 * 0.002 * 15 = 0.03
        assert abs(get_cpr(15, 1.0) - 0.03) < 1e-10

    def test_cpr_month_30(self):
        # 100 PSA: month 30 → 1.0 * 0.002 * 30 = 0.06
        assert abs(get_cpr(30, 1.0) - 0.06) < 1e-10

    def test_cpr_month_31_plateau(self):
        # 100 PSA: month 31+ → 1.0 * 0.06 = 0.06
        assert abs(get_cpr(31, 1.0) - 0.06) < 1e-10
        assert abs(get_cpr(100, 1.0) - 0.06) < 1e-10

    def test_cpr_275_psa(self):
        # 275 PSA: plateau → 2.75 * 0.06 = 0.165
        assert abs(get_cpr(31, 2.75) - 0.165) < 1e-10

    def test_smm_from_cpr(self):
        cpr = 0.06
        expected_smm = 1 - (1 - cpr) ** (1 / 12)
        assert abs(cpr_to_smm(cpr) - expected_smm) < 1e-10

    def test_smm_zero_cpr(self):
        assert cpr_to_smm(0.0) == 0.0
```

**Step 2: Run tests to verify they fail**

Run: `uv run python -m pytest tests/test_mbs.py::TestPSAModel -v`
Expected: FAIL — module not found

**Step 3: Implement PSA functions in `analytics_engine/mbs.py`**

```python
def get_cpr(month: int, psa_speed: float) -> float:
    """CPR under PSA model. Ramps 0.2%/mo for months 1-30, plateaus after."""
    if month <= 30:
        return psa_speed * 0.002 * month
    return psa_speed * 0.06


def cpr_to_smm(cpr: float) -> float:
    """Convert annual CPR to Single Monthly Mortality."""
    return 1 - (1 - cpr) ** (1 / 12)
```

**Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_mbs.py::TestPSAModel -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add analytics_engine/mbs.py tests/test_mbs.py
git commit -m "feat: add PSA prepayment model (get_cpr, cpr_to_smm)"
```

---

### Task 4: MBS Cash Flow Generation and WAL

**Files:**
- Modify: `analytics_engine/mbs.py`
- Modify: `tests/test_mbs.py`

**Step 1: Write the failing tests**

Add to `tests/test_mbs.py`:

```python
from analytics_engine.mbs import generate_mbs_cashflows, compute_wal


class TestMBSCashFlows:
    def test_cashflows_balance_declines(self):
        cfs = generate_mbs_cashflows(0.045, 2.75)  # ~275 PSA
        for i in range(1, len(cfs)):
            assert cfs[i]["balance_bop"] < cfs[i - 1]["balance_bop"]

    def test_cashflows_all_positive(self):
        cfs = generate_mbs_cashflows(0.045, 2.75)
        for cf in cfs:
            assert cf["total_cf"] > 0
            assert cf["interest"] >= 0
            assert cf["total_principal"] > 0

    def test_cashflows_terminate_when_balance_zero(self):
        cfs = generate_mbs_cashflows(0.045, 2.75)
        assert len(cfs) < 360  # high PSA should pay off early

    def test_wal_100_psa(self):
        cfs = generate_mbs_cashflows(0.045, 1.0)  # 100 PSA
        wal = compute_wal(cfs)
        assert abs(wal - 10.94) < 0.5  # ~10.94 years at 100 PSA

    def test_wal_275_psa(self):
        cfs = generate_mbs_cashflows(0.045, 2.75)  # ~275 PSA
        wal = compute_wal(cfs)
        assert abs(wal - 6.0) < 0.5  # ~6 years at ~275 PSA
```

**Step 2: Run tests to verify they fail**

Run: `uv run python -m pytest tests/test_mbs.py::TestMBSCashFlows -v`
Expected: FAIL — functions not defined

**Step 3: Implement in `analytics_engine/mbs.py`**

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_mbs.py::TestMBSCashFlows -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add analytics_engine/mbs.py tests/test_mbs.py
git commit -m "feat: add MBS cash flow generation and WAL calculation"
```

---

### Task 5: PSA Solver and Accrued Interest

**Files:**
- Modify: `analytics_engine/mbs.py`
- Modify: `tests/test_mbs.py`

**Step 1: Write the failing tests**

Add to `tests/test_mbs.py`:

```python
from datetime import date
from analytics_engine.mbs import psa_from_wal, mbs_accrued_interest


class TestPSASolver:
    def test_psa_from_wal_6yr(self):
        psa = psa_from_wal(6.0, 0.045)
        assert abs(psa - 2.7471) < 0.05  # ~274.71 in PSA notation (×100)

    def test_psa_from_wal_roundtrip(self):
        """PSA → WAL → PSA should roundtrip."""
        psa = psa_from_wal(6.0, 0.045)
        cfs = generate_mbs_cashflows(0.045, psa)
        wal = compute_wal(cfs)
        assert abs(wal - 6.0) < 0.01


class TestMBSAccruedInterest:
    def test_accrued_march_15(self):
        # 14 days from March 1 to March 15, ACT/360
        accrued = mbs_accrued_interest(date(2026, 3, 15), 0.045, "ACT/360")
        expected = 100.0 * 0.045 * (14 / 360)
        assert abs(accrued - expected) < 1e-6
        assert abs(accrued - 0.0175) < 0.01  # ~0.0175

    def test_accrued_first_of_month(self):
        # Settlement on 1st → 0 days accrued
        accrued = mbs_accrued_interest(date(2026, 3, 1), 0.045, "ACT/360")
        assert accrued == 0.0
```

**Step 2: Run tests to verify they fail**

Run: `uv run python -m pytest tests/test_mbs.py::TestPSASolver tests/test_mbs.py::TestMBSAccruedInterest -v`
Expected: FAIL — functions not defined

**Step 3: Implement in `analytics_engine/mbs.py`**

```python
from datetime import date
from scipy.optimize import brentq
from analytics_engine.day_count import day_count_fraction


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
```

**Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_mbs.py::TestPSASolver tests/test_mbs.py::TestMBSAccruedInterest -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add analytics_engine/mbs.py tests/test_mbs.py
git commit -m "feat: add PSA solver and MBS accrued interest"
```

---

### Task 6: CFY Solver and `price_mbs()` Pipeline

**Files:**
- Modify: `analytics_engine/mbs.py`
- Modify: `tests/test_mbs.py`

**Step 1: Write the failing tests**

Add to `tests/test_mbs.py`:

```python
from analytics_engine.mbs import solve_cfy, price_mbs
from analytics_engine.models import BondSpec


class TestCFYSolver:
    def test_cfy_bey_benchmark(self):
        """CFY BEY for WAL=6yr, dirty=99.1694 should be ~4.7160%."""
        psa = psa_from_wal(6.0, 0.045)
        cfs = generate_mbs_cashflows(0.045, psa)
        cfy = solve_cfy(cfs, 99.1694)
        assert abs(cfy["cfy_bey"] - 0.04716) < 0.001

    def test_cfy_bey_100_psa(self):
        """CFY BEY at 100 PSA (WAL~10.94) should be ~4.6506%."""
        cfs = generate_mbs_cashflows(0.045, 1.0)
        cfy = solve_cfy(cfs, 99.1694)
        assert abs(cfy["cfy_bey"] - 0.04651) < 0.002


class TestPriceMBS:
    def test_full_pipeline_benchmark(self):
        spec = BondSpec(
            name="B4: MBS", clean_price=99.00, coupon_rate=0.045,
            maturity=date(2032, 3, 15), settlement=date(2026, 3, 15),
            freq=12, day_count="ACT/360",
            bond_type="MBS", wal=6.0,
        )
        result = price_mbs(spec)
        assert abs(result.accrued_interest - 0.0175) < 0.01
        assert abs(result.dirty_price - 99.0175) < 0.02
        assert result.mbs_details is not None
        assert abs(result.mbs_details["psa_speed"] - 2.7471) < 0.05
        assert abs(result.mbs_details["cfy_bey"] - 0.04716) < 0.002
        assert result.ytm > 0  # bullet-equivalent YTM

    def test_mbs_has_ytm(self):
        """MBS should compute YTM via solve_ytm reuse."""
        spec = BondSpec(
            name="B4: MBS", clean_price=99.00, coupon_rate=0.045,
            maturity=date(2032, 3, 15), settlement=date(2026, 3, 15),
            freq=12, day_count="ACT/360",
            bond_type="MBS", wal=6.0,
        )
        result = price_mbs(spec)
        assert result.ytm is not None
        assert result.ytm > 0
```

**Step 2: Run tests to verify they fail**

Run: `uv run python -m pytest tests/test_mbs.py::TestCFYSolver tests/test_mbs.py::TestPriceMBS -v`
Expected: FAIL — functions not defined

**Step 3: Implement in `analytics_engine/mbs.py`**

```python
from analytics_engine.models import BondResult, BondSpec
from analytics_engine.solver import solve_ytm


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


def price_mbs(spec: BondSpec) -> BondResult:
    """MBS passthrough pricing pipeline."""
    current_face = 100.0
    term_months = 360
    seasoning = 0
    wal = spec.wal

    # Step 1: Solve PSA from WAL
    psa_speed = psa_from_wal(wal, spec.coupon_rate, term_months, current_face, seasoning)

    # Step 2: Accrued interest
    accrued = mbs_accrued_interest(spec.settlement, spec.coupon_rate, spec.day_count, current_face)
    dirty_price = spec.clean_price + accrued

    # Step 3: Cash flows and CFY
    cash_flows = generate_mbs_cashflows(spec.coupon_rate, psa_speed, term_months, current_face, seasoning)
    wal_computed = compute_wal(cash_flows)
    cfy = solve_cfy(cash_flows, dirty_price)

    # Step 4: Bullet-equivalent YTM via existing solver
    ytm_result = solve_ytm(spec)

    result = BondResult(
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
    return result
```

**Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_mbs.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add analytics_engine/mbs.py tests/test_mbs.py
git commit -m "feat: add CFY solver and price_mbs pipeline"
```

---

### Task 7: Dispatch Routing and CLI Output

**Files:**
- Modify: `analytics_engine/pricing.py`
- Modify: `analytics_engine/cli.py`
- Modify: `tests/test_pricing.py`

**Step 1: Write the failing test**

Add to `tests/test_pricing.py`:

```python
def test_analyze_bond_routes_mbs():
    spec = BondSpec(
        name="B4: MBS", clean_price=99.00, coupon_rate=0.045,
        maturity=date(2032, 3, 15), settlement=date(2026, 3, 15),
        freq=12, day_count="ACT/360",
        bond_type="MBS", wal=6.0,
    )
    result = analyze_bond(spec)
    assert result.mbs_details is not None
    assert result.mbs_details["psa_speed"] > 0
```

**Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_pricing.py::test_analyze_bond_routes_mbs -v`
Expected: FAIL — mbs_details is None (dispatch not wired)

**Step 3: Update `analytics_engine/pricing.py`**

```python
from analytics_engine.models import BondSpec, BondResult
from analytics_engine.solver import solve_ytm
from analytics_engine.mbs import price_mbs


def analyze_bond(spec: BondSpec) -> BondResult:
    """Compute analytics for a single bond, routing MBS to dedicated pricer."""
    if spec.bond_type and "mbs" in spec.bond_type.lower():
        return price_mbs(spec)
    return solve_ytm(spec)


def analyze_portfolio(specs: list[BondSpec]) -> list[BondResult]:
    """Analyze a list of bonds, returning a result for each."""
    return [analyze_bond(spec) for spec in specs]
```

**Step 4: Update `analytics_engine/cli.py`**

Update B4 bond definition and output formatter to include CFY/PSA columns:

```python
from datetime import date

from analytics_engine.models import BondSpec
from analytics_engine.pricing import analyze_portfolio

BONDS = [
    BondSpec("B1: UST", 98.25, 0.035, date(2032, 6, 30), date(2026, 3, 15), 2, "ACT/ACT"),
    BondSpec("B2: IG Corp", 101.40, 0.0525, date(2029, 9, 15), date(2026, 3, 15), 2, "30/360"),
    BondSpec("B3: HY Corp", 92.10, 0.08, date(2028, 12, 1), date(2026, 3, 15), 2, "30/360"),
    BondSpec("B4: MBS", 99.00, 0.045, date(2032, 3, 15), date(2026, 3, 15), 12, "ACT/360",
             bond_type="MBS", wal=6.0),
    BondSpec("B5: Zero Coupon", 95.00, 0.0, date(2027, 3, 15), date(2026, 3, 15), 1, "ACT/ACT"),
]


def main() -> None:
    results = analyze_portfolio(BONDS)
    col_widths = (20, 18, 13, 10, 10, 9)
    header = (
        f"{'Bond':<{col_widths[0]}} | "
        f"{'Accrued Interest':>{col_widths[1]}} | "
        f"{'Dirty Price':>{col_widths[2]}} | "
        f"{'YTM (%)':>{col_widths[3]}} | "
        f"{'CFY (%)':>{col_widths[4]}} | "
        f"{'PSA':>{col_widths[5]}}"
    )
    separator = "-" * len(header)
    print()
    print(header)
    print(separator)
    for r in results:
        is_mbs = r.mbs_details is not None
        cfy_str = f"{r.mbs_details['cfy_bey'] * 100:>{col_widths[4] - 1}.4f}%" if is_mbs else f"{'#':>{col_widths[4]}}"
        psa_str = f"{r.mbs_details['psa_speed'] * 100:>{col_widths[5]}.2f}" if is_mbs else f"{'#':>{col_widths[5]}}"
        print(
            f"{r.spec.name:<{col_widths[0]}} | "
            f"{r.accrued_interest:>{col_widths[1]}.4f} | "
            f"{r.dirty_price:>{col_widths[2]}.4f} | "
            f"{r.ytm * 100:>{col_widths[3] - 1}.4f}% | "
            f"{cfy_str} | "
            f"{psa_str}"
        )
    print()


if __name__ == "__main__":
    main()
```

**Step 5: Run full test suite**

Run: `uv run python -m pytest -v`
Expected: All tests PASS (old + new)

**Step 6: Run CLI to verify output**

Run: `uv run python -m analytics_engine`
Expected output matches benchmark table:
```
 Bond            | Accrued Interest | Dirty Price |    YTM (%) |    CFY (%) |     PSA
--------------------------------------------------------------------------------------
B1: UST          |           0.7212 |     98.9712 |    3.8119% |          # |       #
B2: IG Corp      |           0.0000 |    101.4000 |    4.8106% |          # |       #
B3: HY Corp      |           2.3111 |     94.4111 |   11.4601% |          # |       #
B4: MBS          |           0.1694 |     99.1694 |    4.6725% |    4.7160% |  274.71
B5: Zero Coupon  |           0.0000 |     95.0000 |    5.2632% |          # |       #
```

**Step 7: Commit**

```bash
git add analytics_engine/pricing.py analytics_engine/cli.py tests/test_pricing.py
git commit -m "feat: wire MBS dispatch and update CLI with CFY/PSA columns"
```
