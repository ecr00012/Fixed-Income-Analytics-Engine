from datetime import date
from analytics_engine.cash_flows import generate_coupon_schedule, compute_accrued_interest


class TestCouponSchedule:
    def test_semiannual_bond(self):
        """B1: UST 3.5%, maturity 2032-06-30, settlement 2026-03-15, freq 2"""
        schedule = generate_coupon_schedule(
            settlement=date(2026, 3, 15),
            maturity=date(2032, 6, 30),
            freq=2,
        )
        assert len(schedule) > 0
        assert schedule[-1] == date(2032, 6, 30)
        assert all(d > date(2026, 3, 15) for d in schedule)

    def test_monthly_bond(self):
        """B4: MBS, freq 12, maturity 2032-03-15, settlement 2026-03-15"""
        schedule = generate_coupon_schedule(
            settlement=date(2026, 3, 15),
            maturity=date(2032, 3, 15),
            freq=12,
        )
        # 6 years × 12 = 72 monthly coupons
        assert len(schedule) == 72
        assert schedule[-1] == date(2032, 3, 15)

    def test_zero_coupon(self):
        """Zero coupon bonds have no coupons"""
        schedule = generate_coupon_schedule(
            settlement=date(2026, 3, 15),
            maturity=date(2027, 3, 15),
            freq=0,
        )
        assert schedule == []
        
    def test_leap_year(self):
        """Test that the coupon schedule handles leap years correctly"""
        schedule = generate_coupon_schedule(
            settlement=date(2027, 2, 15),
            maturity=date(2028, 2, 29),
            freq=2,
        )
        assert schedule == [
            date(2027, 2, 28),
            date(2027, 8, 29),
            date(2028, 2, 29),
        ]

    def test_first_of_month(self):
        """MBS bond principal repayment rate is the 1st of the month"""
        schedule = generate_coupon_schedule(
            settlement=date(2026, 3, 15),
            maturity=date(2026, 6, 1),
            freq=12,
        )   
        assert schedule == [
            date(2026, 4, 1),
            date(2026, 5, 1),
            date(2026, 6, 1),
        ]

class TestAccruedInterest:
    def test_settlement_on_coupon_date(self):
        """Settlement on a coupon date → accrued = 0"""
        accrued = compute_accrued_interest(
            settlement=date(2026, 3, 15),
            coupon_rate=0.0525,
            freq=2,
            day_count="30/360",
            prev_coupon=date(2026, 3, 15),
            next_coupon=date(2026, 9, 15),
        )
        assert accrued == 0.0

    def test_zero_coupon_accrued(self):
        """Zero coupon bonds have 0 accrued interest"""
        accrued = compute_accrued_interest(
            settlement=date(2026, 3, 15),
            coupon_rate=0.0,
            freq=0,
            day_count="ACT/ACT",
            prev_coupon=None,
            next_coupon=None,
        )
        assert accrued == 0.0

    def test_mid_period_accrued(self):
        """Midway through a 6-month coupon period → accrued ≈ half-coupon"""
        # 5% semiannual bond, 30/360: coupon = 2.5 per 100 face
        # prev=2026-01-15, settlement=2026-04-15 (90 days in), next=2026-07-15 (180 days)
        accrued = compute_accrued_interest(
            settlement=date(2026, 4, 15),
            coupon_rate=0.05,
            freq=2,
            day_count="30/360",
            prev_coupon=date(2026, 1, 15),
            next_coupon=date(2026, 7, 15),
        )
        # 90/180 of the coupon payment = 1.25
        assert abs(accrued - 1.25) < 1e-6
