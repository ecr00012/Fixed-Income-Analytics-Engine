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
