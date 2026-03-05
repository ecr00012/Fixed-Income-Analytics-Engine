from datetime import date
from analytics_engine.models import BondSpec, BondResult


def test_bond_spec_creation():
    spec = BondSpec(
        name="B1: UST",
        clean_price=98.25,
        coupon_rate=0.035,
        maturity=date(2032, 6, 30),
        settlement=date(2026, 3, 15),
        freq=2,
        day_count="ACT/ACT",
    )
    assert spec.name == "B1: UST"
    assert spec.clean_price == 98.25
    assert spec.coupon_rate == 0.035
    assert spec.freq == 2


def test_bond_result_creation():
    spec = BondSpec(
        name="B5: Zero Coupon",
        clean_price=95.00,
        coupon_rate=0.0,
        maturity=date(2027, 3, 15),
        settlement=date(2026, 3, 15),
        freq=1,
        day_count="ACT/ACT",
    )
    result = BondResult(spec=spec, accrued_interest=0.0, dirty_price=95.00, ytm=0.05263)
    assert result.accrued_interest == 0.0
    assert result.dirty_price == 95.00
    assert result.ytm == 0.05263
