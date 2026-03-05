from datetime import date
from analytics_engine.models import BondSpec
from analytics_engine.solver import price_from_yield, solve_ytm


class TestPriceFromYield:
    def test_par_bond(self):
        """A bond priced at par should have price ≈ 100 when YTM == coupon rate."""
        price, dpdy = price_from_yield(
            ytm=0.05,
            coupon_rate=0.05,
            settlement=date(2026, 3, 15),
            maturity=date(2028, 3, 15),
            freq=2,
            day_count="30/360",
        )
        assert abs(price - 100.0) < 0.01

    def test_derivative_is_negative(self):
        """Price is a decreasing function of yield → derivative must be negative."""
        _, dpdy = price_from_yield(
            ytm=0.05,
            coupon_rate=0.05,
            settlement=date(2026, 3, 15),
            maturity=date(2028, 3, 15),
            freq=2,
            day_count="30/360",
        )
        assert dpdy < 0

    def test_higher_yield_lower_price(self):
        """Fundamental bond math: higher yield → lower price."""
        price_low, _ = price_from_yield(
            ytm=0.03,
            coupon_rate=0.05,
            settlement=date(2026, 3, 15),
            maturity=date(2028, 3, 15),
            freq=2,
            day_count="30/360",
        )
        price_high, _ = price_from_yield(
            ytm=0.07,
            coupon_rate=0.05,
            settlement=date(2026, 3, 15),
            maturity=date(2028, 3, 15),
            freq=2,
            day_count="30/360",
        )
        assert price_low > price_high


class TestSolveYtm:
    def test_par_bond_ytm(self):
        """Bond at par → YTM should equal coupon rate."""
        spec = BondSpec(
            name="Par Bond",
            clean_price=100.0,
            coupon_rate=0.05,
            maturity=date(2028, 3, 15),
            settlement=date(2026, 3, 15),
            freq=2,
            day_count="30/360",
        )
        result = solve_ytm(spec)
        assert abs(result.ytm - 0.05) < 1e-6

    def test_discount_bond_ytm(self):
        """Bond below par → YTM should exceed coupon rate."""
        spec = BondSpec(
            name="Discount Bond",
            clean_price=95.0,
            coupon_rate=0.05,
            maturity=date(2028, 3, 15),
            settlement=date(2026, 3, 15),
            freq=2,
            day_count="30/360",
        )
        result = solve_ytm(spec)
        assert result.ytm > 0.05

    def test_premium_bond_ytm(self):
        """Bond above par → YTM should be below coupon rate."""
        spec = BondSpec(
            name="Premium Bond",
            clean_price=105.0,
            coupon_rate=0.05,
            maturity=date(2028, 3, 15),
            settlement=date(2026, 3, 15),
            freq=2,
            day_count="30/360",
        )
        result = solve_ytm(spec)
        assert result.ytm < 0.05

    def test_zero_coupon_ytm(self):
        """B5: Zero coupon, clean price 95, 1 year → closed-form YTM ≈ 5.263%."""
        spec = BondSpec(
            name="B5: Zero Coupon",
            clean_price=95.0,
            coupon_rate=0.0,
            maturity=date(2027, 3, 15),
            settlement=date(2026, 3, 15),
            freq=1,
            day_count="ACT/ACT",
        )
        result = solve_ytm(spec)
        assert abs(result.ytm - 0.05263) < 1e-4
        assert result.accrued_interest == 0.0
        assert result.dirty_price == 95.0

    def test_convergence_hy_corp(self):
        """B3: HY Corp should converge to a positive yield."""
        spec = BondSpec(
            name="B3: HY Corp",
            clean_price=92.10,
            coupon_rate=0.08,
            maturity=date(2028, 12, 1),
            settlement=date(2026, 3, 15),
            freq=2,
            day_count="30/360",
        )
        result = solve_ytm(spec)
        assert result.ytm > 0
