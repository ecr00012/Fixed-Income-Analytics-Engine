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

