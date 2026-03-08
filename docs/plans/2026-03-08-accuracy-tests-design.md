# Accuracy & Robustness Test Suite — Design

## Goal
Create 5 new test bonds with significantly different parameters from the existing portfolio (B1–B5) and independently hand-derive all expected values. The test file validates that the analytics engine reproduces these independently computed results to high precision.

## Bond Specifications

| ID  | Type           | Coupon | Maturity    | Settlement  | Freq | Day Count | Clean Price  | YTM     |
|-----|----------------|--------|-------------|-------------|------|-----------|--------------|---------|
| T6  | UST 10Y        | 1.5%   | 2031-09-15  | 2026-09-15  | 2    | 30/360    | 86.700675    | 4.500%  |
| T7  | IG Corp Q      | 3.0%   | 2030-09-15  | 2026-09-15  | 4    | 30/360    | 91.078295    | 5.500%  |
| T8  | HY Short Prem  | 12.0%  | 2027-12-01  | 2026-07-15  | 2    | 30/360    | 105.100322   | 8.000%  |
| T9  | MBS Short WAL  | 6.0%   | 2029-12-15  | 2026-06-15  | 12   | ACT/360   | 101.50       | 5.374%  |
| T10 | Zero 10Y       | 0.0%   | 2036-03-01  | 2026-03-01  | 1    | ACT/ACT   | 55.00        | 6.155%  |

### How each bond differs from its original

- **T6 vs B1 (UST):** Coupon 1.5% vs 3.5%, day count 30/360 vs ACT/ACT, settlement Sep vs Mar, deep discount vs near-par
- **T7 vs B2 (IG Corp):** Coupon 3.0% vs 5.25%, **freq 4 (quarterly)** vs 2, discount vs premium
- **T8 vs B3 (HY Corp):** Coupon 12% vs 8%, short 1.4yr vs 2.7yr, premium vs discount, mid-period settlement
- **T9 vs B4 (MBS):** Coupon 6% vs 4.5%, WAL 3.5yr vs 6yr, premium vs slight-discount, different settlement
- **T10 vs B5 (Zero):** 10-year vs 1-year, price 55 vs 95+, settlement Mar 1 vs Mar 15

---

## Hand-Derived Expected Values

### T6: UST 10Y, Deep Discount
- **Parameters:** Settlement on coupon date → accrued = 0. 10 semiannual periods. 30/360 gives t = 1,2,...,10 exactly.
- **Method:** Reverse-engineered — chose YTM = 4.5%, computed dirty price via PV of coupon annuity + PV of principal.
- **Results:** Accrued = 0.0, Dirty = Clean = **86.7006754767**, YTM = 4.5000%

### T7: IG Corp Quarterly
- **Parameters:** Settlement on coupon date → accrued = 0. 16 quarterly periods. 30/360 gives t = 1,2,...,16.
- **Method:** Reverse-engineered — chose YTM = 5.5%.
- **Results:** Accrued = 0.0, Dirty = Clean = **91.0782952892**, YTM = 5.5000%

### T8: HY Short, Premium, Mid-Period
- **Parameters:** Settlement 2026-07-15, prev coupon 2026-06-01, next coupon 2026-12-01.
- **Accrued:** 30/360 fraction = DCF(Jun1→Jul15) / DCF(Jun1→Dec1) = (44/360) / (180/360) = 44/180 = 0.2444. Coupon = 12%/2 × 100 = 6.0. Accrued = 6.0 × 0.2444 = **1.4667**.
- **Time fractions:** t = 0.7556, 1.7556, 2.7556 (fractional periods from mid-period settlement).
- **Dirty price at YTM = 8%:** **106.5669882069**
- **Clean:** 106.5670 − 1.4667 = **105.1003215402**

### T10: Zero Coupon 10Y
- **Parameters:** Clean = 55.00, no accrued. ACT/ACT time fraction.
- **Closed form:** t = (2036-03-01 − 2026-03-01).days / 365 = 3653/365 = 10.0082yr. YTM = (100/55)^(1/10.0082) − 1 = **6.1555%**

### T9: MBS Short WAL
- **PSA model:** PSA ramp (CPR = PSA × 0.002 × month for month ≤ 30, plateau at PSA × 0.06). Bisected PSA speed to hit WAL = 3.5yr → PSA = **5.6885** (~568.85% PSA).
- **Accrued:** From June 1 to June 15 = 14 days ACT/360. 100 × 0.06 × 14/360 = **0.2333**
- **Dirty:** 101.50 + 0.2333 = **101.7333**
- **CFY (BEY):** Bisected monthly yield → **5.4956%** BEY
- **Bullet YTM:** **5.3736%**
- **WAL:** 3.5000 years (by construction)

---

## Test Structure

### File: `tests/test_accuracy.py` (NEW — no existing files modified)

```
class TestT6USTDeepDiscount      — 3 assertions (accrued, dirty, ytm)
class TestT7IGCorpQuarterly      — 3 assertions (accrued, dirty, ytm)
class TestT8HYShortPremium       — 3 assertions (accrued, dirty, ytm)
class TestT9MBSShortWAL          — 6 assertions (accrued, dirty, ytm, psa, cfy_bey, wal)
class TestT10ZeroCoupon10Y       — 3 assertions (accrued, dirty, ytm)
```

### Tolerances
- Accrued interest, dirty price, clean price: **±0.0001** (4 decimal places)
- YTM: **±1e-4** (0.01 percentage points)
- PSA speed: **±0.05**
- CFY BEY: **±0.002**
- WAL: **±0.01**

---

## Verification Plan

### Automated Tests
```bash
uv run python -m pytest tests/test_accuracy.py -v
```

### Existing Tests (regression check)
```bash
uv run python -m pytest tests/ -v
```
All 52 existing tests must continue to pass. The new file adds ~18 assertions bringing total to ~70.
