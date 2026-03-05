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


class TestMBSCashFlows:
    def test_cashflows_balance_declines(self):
        from analytics_engine.mbs import generate_mbs_cashflows
        cfs = generate_mbs_cashflows(0.045, 2.75)
        for i in range(1, len(cfs)):
            assert cfs[i]["balance_bop"] < cfs[i - 1]["balance_bop"]

    def test_cashflows_all_positive(self):
        from analytics_engine.mbs import generate_mbs_cashflows
        cfs = generate_mbs_cashflows(0.045, 2.75)
        for cf in cfs:
            assert cf["total_cf"] > 0
            assert cf["interest"] >= 0
            assert cf["total_principal"] > 0

    def test_cashflows_principal_fully_returned(self):
        from analytics_engine.mbs import generate_mbs_cashflows
        cfs = generate_mbs_cashflows(0.045, 2.75)
        total_principal = sum(cf["total_principal"] for cf in cfs)
        assert abs(total_principal - 100.0) < 0.01  # virtually all principal returned

    def test_wal_100_psa(self):
        from analytics_engine.mbs import generate_mbs_cashflows, compute_wal
        cfs = generate_mbs_cashflows(0.045, 1.0)
        wal = compute_wal(cfs)
        assert abs(wal - 10.94) < 0.5

    def test_wal_275_psa(self):
        from analytics_engine.mbs import generate_mbs_cashflows, compute_wal
        cfs = generate_mbs_cashflows(0.045, 2.75)
        wal = compute_wal(cfs)
        assert abs(wal - 6.0) < 0.5


class TestPSASolver:
    def test_psa_from_wal_6yr(self):
        from analytics_engine.mbs import psa_from_wal
        psa = psa_from_wal(6.0, 0.045)
        assert abs(psa - 2.7471) < 0.05

    def test_psa_from_wal_roundtrip(self):
        from analytics_engine.mbs import psa_from_wal, generate_mbs_cashflows, compute_wal
        psa = psa_from_wal(6.0, 0.045)
        cfs = generate_mbs_cashflows(0.045, psa)
        wal = compute_wal(cfs)
        assert abs(wal - 6.0) < 0.01


class TestMBSAccruedInterest:
    def test_accrued_march_15(self):
        from datetime import date
        from analytics_engine.mbs import mbs_accrued_interest
        accrued = mbs_accrued_interest(date(2026, 3, 15), 0.045, "ACT/360")
        expected = 100.0 * 0.045 * (14 / 360)
        assert abs(accrued - expected) < 1e-6

    def test_accrued_first_of_month(self):
        from datetime import date
        from analytics_engine.mbs import mbs_accrued_interest
        accrued = mbs_accrued_interest(date(2026, 3, 1), 0.045, "ACT/360")
        assert accrued == 0.0

