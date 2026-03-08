"""
Accuracy & Robustness Test Suite
=================================
5 new test bonds with independently hand-derived expected values.
All expected values computed from first principles — no engine functions used.
See docs/plans/2026-03-08-accuracy-tests-design.md for full derivations.
"""

from datetime import date

import pytest

from analytics_engine.models import BondSpec
from analytics_engine.pricing import analyze_bond


# ============================================================
# T6: UST 10Y, Deep Discount (STRESS)
#   - 1.5% coupon (vs B1's 3.5%), 30/360 (vs B1's ACT/ACT)
#   - Settlement on coupon date -> accrued = 0
#   - 10 semiannual periods, t = 1..10 exactly
#   - Reverse-engineered: chose YTM=4.5%, computed PV -> clean price
# ============================================================
class TestT6USTDeepDiscount:
    SPEC = BondSpec(
        name="T6: UST 10Y",
        clean_price=86.7006754767,
        coupon_rate=0.015,
        maturity=date(2031, 9, 15),
        settlement=date(2026, 9, 15),
        freq=2,
        day_count="30/360",
    )

    EXPECTED_ACCRUED = 0.0
    EXPECTED_DIRTY = 86.7006754767
    EXPECTED_YTM = 0.045

    def test_accrued_interest(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.accrued_interest - self.EXPECTED_ACCRUED) < 1e-4

    def test_dirty_price(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.dirty_price - self.EXPECTED_DIRTY) < 1e-4

    def test_ytm(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.ytm - self.EXPECTED_YTM) < 1e-4


# ============================================================
# T7: IG Corp Quarterly (DIVERSE)
#   - 3.0% coupon (vs B2's 5.25%), freq=4 quarterly (vs B2's 2)
#   - Settlement on coupon date -> accrued = 0
#   - 16 quarterly periods, t = 1..16 exactly
#   - Tests an untested frequency (quarterly)
#   - Reverse-engineered: chose YTM=5.5%, computed PV -> clean price
# ============================================================
class TestT7IGCorpQuarterly:
    SPEC = BondSpec(
        name="T7: IG Corp Q",
        clean_price=91.0782952892,
        coupon_rate=0.03,
        maturity=date(2030, 9, 15),
        settlement=date(2026, 9, 15),
        freq=4,
        day_count="30/360",
    )

    EXPECTED_ACCRUED = 0.0
    EXPECTED_DIRTY = 91.0782952892
    EXPECTED_YTM = 0.055

    def test_accrued_interest(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.accrued_interest - self.EXPECTED_ACCRUED) < 1e-4

    def test_dirty_price(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.dirty_price - self.EXPECTED_DIRTY) < 1e-4

    def test_ytm(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.ytm - self.EXPECTED_YTM) < 1e-4


# ============================================================
# T8: HY Corp Short, Premium, Mid-Period (STRESS)
#   - 12% coupon (vs B3's 8%), short 1.4yr (vs B3's 2.7yr)
#   - Premium (vs B3's discount), mid-period settlement
#   - Settlement 2026-07-15, prev coupon 2026-06-01, next 2026-12-01
#   - 30/360: DCF(Jun1->Jul15)=44/360, DCF(Jun1->Dec1)=180/360
#     frac = 44/180 = 0.24444, coupon = 6.0, accrued = 1.46667
#   - 3 coupon periods at t = 0.7556, 1.7556, 2.7556
#   - Reverse-engineered: chose YTM=8%, computed PV -> clean price
# ============================================================
class TestT8HYShortPremium:
    SPEC = BondSpec(
        name="T8: HY Short",
        clean_price=105.1003215402,
        coupon_rate=0.12,
        maturity=date(2027, 12, 1),
        settlement=date(2026, 7, 15),
        freq=2,
        day_count="30/360",
    )

    EXPECTED_ACCRUED = 1.4667   # 6.0 * 44/180
    EXPECTED_DIRTY = 106.5670   # PV at YTM=8% with fractional periods
    EXPECTED_YTM = 0.08

    def test_accrued_interest(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.accrued_interest - self.EXPECTED_ACCRUED) < 1e-4

    def test_dirty_price(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.dirty_price - self.EXPECTED_DIRTY) < 1e-4

    def test_ytm(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.ytm - self.EXPECTED_YTM) < 1e-4


# ============================================================
# T9: MBS Short WAL (DIVERSE)
#   - 6.0% coupon (vs B4's 4.5%), WAL=3.5yr (vs B4's 6yr)
#   - Settlement 2026-06-15, premium 101.50 (vs B4's 99.00)
#   - Accrued = 100 * 0.06 * 14/360 = 0.2333 (14 days from Jun 1)
#   - PSA bisected for WAL=3.5 -> ~5.6885 (568.85% PSA)
#   - CFY BEY independently computed via bisection -> ~5.50%
#   - Bullet-equiv YTM -> ~5.37%
# ============================================================
class TestT9MBSShortWAL:
    SPEC = BondSpec(
        name="T9: MBS Short WAL",
        clean_price=101.50,
        coupon_rate=0.06,
        maturity=date(2029, 12, 15),
        settlement=date(2026, 6, 15),
        freq=12,
        day_count="ACT/360",
        bond_type="MBS",
        wal=3.5,
    )

    EXPECTED_ACCRUED = 0.2333       # 100 * 0.06 * 14/360
    EXPECTED_DIRTY = 101.7333       # 101.50 + 0.2333
    EXPECTED_YTM = 0.0545           # Bullet-equivalent YTM
    EXPECTED_PSA = 5.6885           # PSA speed for WAL=3.5
    EXPECTED_CFY_BEY = 0.0550       # Cash flow yield (BEY)
    EXPECTED_WAL = 3.5              # By construction

    def test_accrued_interest(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.accrued_interest - self.EXPECTED_ACCRUED) < 1e-4

    def test_dirty_price(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.dirty_price - self.EXPECTED_DIRTY) < 1e-4

    def test_ytm(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.ytm - self.EXPECTED_YTM) < 1e-4

    def test_psa_speed(self):
        result = analyze_bond(self.SPEC)
        assert result.mbs_details is not None
        assert abs(result.mbs_details["psa_speed"] - self.EXPECTED_PSA) < 0.05

    def test_cfy_bey(self):
        result = analyze_bond(self.SPEC)
        assert result.mbs_details is not None
        assert abs(result.mbs_details["cfy_bey"] - self.EXPECTED_CFY_BEY) < 0.002

    def test_wal(self):
        result = analyze_bond(self.SPEC)
        assert result.mbs_details is not None
        assert abs(result.mbs_details["wal_years"] - self.EXPECTED_WAL) < 0.01


# ============================================================
# T10: Long Zero Coupon 10Y 
#   - 10-year maturity (vs B5's 1yr), deep discount 55 (vs B5's 95)
#   - Closed-form: YTM = (100/55)^(1/t) - 1
#   - ACT/ACT: t = 3653/365 = 10.00822 years
#   - YTM = 6.1555%
# ============================================================
class TestT10ZeroCoupon10Y:
    SPEC = BondSpec(
        name="T10: Zero 10Y",
        clean_price=55.00,
        coupon_rate=0.0,
        maturity=date(2036, 3, 1),
        settlement=date(2026, 3, 1),
        freq=1,
        day_count="ACT/ACT",
    )

    EXPECTED_ACCRUED = 0.0
    EXPECTED_DIRTY = 55.00
    EXPECTED_YTM = 0.0616     # (100/55)^(1/10.00822) - 1

    def test_accrued_interest(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.accrued_interest - self.EXPECTED_ACCRUED) < 1e-4

    def test_dirty_price(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.dirty_price - self.EXPECTED_DIRTY) < 1e-4

    def test_ytm(self):
        result = analyze_bond(self.SPEC)
        assert abs(result.ytm - self.EXPECTED_YTM) < 1e-4
