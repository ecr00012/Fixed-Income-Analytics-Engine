from datetime import date
from analytics_engine.models import BondSpec
from analytics_engine.pricing import analyze_bond, analyze_portfolio


class TestAnalyzeBond:
    def test_returns_bond_result_with_positive_ytm(self):
        spec = BondSpec(
            name="B1: UST",
            clean_price=98.25,
            coupon_rate=0.035,
            maturity=date(2032, 6, 30),
            settlement=date(2026, 3, 15),
            freq=2,
            day_count="ACT/ACT",
        )
        result = analyze_bond(spec)
        assert result.spec == spec
        assert result.dirty_price >= spec.clean_price
        assert result.ytm > 0

    def test_dirty_price_equals_clean_plus_accrued(self):
        spec = BondSpec(
            name="B2: IG Corp",
            clean_price=101.40,
            coupon_rate=0.0525,
            maturity=date(2029, 9, 15),
            settlement=date(2026, 3, 15),
            freq=2,
            day_count="30/360",
        )
        result = analyze_bond(spec)
        assert abs(result.dirty_price - (result.spec.clean_price + result.accrued_interest)) < 1e-10


class TestAnalyzePortfolio:
    def test_all_five_bonds_produce_results(self):
        """Integration: all 5 target bonds must converge to positive yields."""
        specs = [
            BondSpec("B1: UST", 98.25, 0.035, date(2032, 6, 30), date(2026, 3, 15), 2, "ACT/ACT"),
            BondSpec("B2: IG Corp", 101.40, 0.0525, date(2029, 9, 15), date(2026, 3, 15), 2, "30/360"),
            BondSpec("B3: HY Corp", 92.10, 0.08, date(2028, 12, 1), date(2026, 3, 15), 2, "30/360"),
            BondSpec("B4: MBS", 99.00, 0.045, date(2032, 3, 15), date(2026, 3, 15), 12, "ACT/360"),
            BondSpec("B5: Zero Coupon", 95.00, 0.0, date(2027, 3, 15), date(2026, 3, 15), 1, "ACT/ACT"),
        ]
        results = analyze_portfolio(specs)
        assert len(results) == 5
        for r in results:
            assert r.ytm > 0
            assert r.dirty_price > 0

    def test_zero_coupon_has_no_accrued_interest(self):
        specs = [
            BondSpec("B5: Zero Coupon", 95.00, 0.0, date(2027, 3, 15), date(2026, 3, 15), 1, "ACT/ACT"),
        ]
        results = analyze_portfolio(specs)
        assert results[0].accrued_interest == 0.0


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

