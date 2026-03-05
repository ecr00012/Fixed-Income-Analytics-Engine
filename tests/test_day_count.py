from datetime import date
import pytest
from analytics_engine.day_count import day_count_fraction


class TestActAct:
    def test_non_leap_year(self):
        # 2026-01-01 to 2026-07-01 = 181 days / 365
        result = day_count_fraction(date(2026, 1, 1), date(2026, 7, 1), "ACT/ACT")
        assert abs(result - 181 / 365) < 1e-10

    def test_leap_year(self):
        # 2028 is a leap year: 2028-01-01 to 2028-07-01 = 182 days / 366
        result = day_count_fraction(date(2028, 1, 1), date(2028, 7, 1), "ACT/ACT")
        assert abs(result - 182 / 366) < 1e-10

    def test_same_date(self):
        result = day_count_fraction(date(2026, 3, 15), date(2026, 3, 15), "ACT/ACT")
        assert result == 0.0


class TestThirty360:
    def test_standard(self):
        # 30/360: 2026-01-15 to 2026-07-15 = 6 months = 180/360 = 0.5
        result = day_count_fraction(date(2026, 1, 15), date(2026, 7, 15), "30/360")
        assert abs(result - 0.5) < 1e-10

    def test_month_end(self):
        # 2026-01-31 to 2026-02-28: 30/360 convention
        # d1=min(31,30)=30, d2=28 → days=(0*360 + 1*30 + (28-30)) = 28 → 28/360
        result = day_count_fraction(date(2026, 1, 31), date(2026, 2, 28), "30/360")
        assert abs(result - 28 / 360) < 1e-10


class TestAct360:
    def test_standard(self):
        # 2026-01-01 to 2026-07-01 = 181 actual days / 360
        result = day_count_fraction(date(2026, 1, 1), date(2026, 7, 1), "ACT/360")
        assert abs(result - 181 / 360) < 1e-10

    def test_same_date(self):
        result = day_count_fraction(date(2026, 3, 15), date(2026, 3, 15), "ACT/360")
        assert result == 0.0


def test_invalid_convention():
    with pytest.raises(ValueError):
        day_count_fraction(date(2026, 1, 1), date(2026, 7, 1), "INVALID")
