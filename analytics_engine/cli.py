from datetime import date

from analytics_engine.models import BondSpec
from analytics_engine.pricing import analyze_portfolio

BONDS = [
    BondSpec("B1: UST", 98.25, 0.035, date(2032, 6, 30), date(2026, 3, 15), 2, "ACT/ACT"),
    BondSpec("B2: IG Corp", 101.40, 0.0525, date(2029, 9, 15), date(2026, 3, 15), 2, "30/360"),
    BondSpec("B3: HY Corp", 92.10, 0.08, date(2028, 12, 1), date(2026, 3, 15), 2, "30/360"),
    BondSpec("B4: MBS", 99.00, 0.045, date(2032, 3, 15), date(2026, 3, 15), 12, "ACT/360",
             bond_type="MBS", wal=6.0),
    BondSpec("B5: Zero Coupon", 95.00, 0.0, date(2027, 3, 15), date(2026, 3, 15), 1, "ACT/ACT"),
]


def main() -> None:
    results = analyze_portfolio(BONDS)
    col_widths = (20, 18, 13, 10, 10, 9)
    header = (
        f"{'Bond':<{col_widths[0]}} | "
        f"{'Accrued Interest':>{col_widths[1]}} | "
        f"{'Dirty Price':>{col_widths[2]}} | "
        f"{'YTM (%)':>{col_widths[3]}} | "
        f"{'CFY (%)':>{col_widths[4]}} | "
        f"{'PSA':>{col_widths[5]}}"
    )
    separator = "-" * len(header)
    print()
    print(header)
    print(separator)
    for r in results:
        is_mbs = r.mbs_details is not None
        cfy_str = f"{r.mbs_details['cfy_bey'] * 100:>{col_widths[4] - 1}.4f}%" if is_mbs else f"{'#':>{col_widths[4]}}"
        psa_str = f"{r.mbs_details['psa_speed'] * 100:>{col_widths[5]}.2f}" if is_mbs else f"{'#':>{col_widths[5]}}"
        print(
            f"{r.spec.name:<{col_widths[0]}} | "
            f"{r.accrued_interest:>{col_widths[1]}.4f} | "
            f"{r.dirty_price:>{col_widths[2]}.4f} | "
            f"{r.ytm * 100:>{col_widths[3] - 1}.4f}% | "
            f"{cfy_str} | "
            f"{psa_str}"
        )
    print()


if __name__ == "__main__":
    main()
