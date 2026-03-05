from datetime import date
from analytics_engine.solver import price_from_yield


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
