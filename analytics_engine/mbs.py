"""MBS Passthrough Pricer — PSA model, cash flows, CFY, and pricing pipeline."""

from __future__ import annotations


def get_cpr(month: int, psa_speed: float) -> float:
    """CPR under PSA model. Ramps 0.2%/mo for months 1-30, plateaus after."""
    if month <= 30:
        return psa_speed * 0.002 * month
    return psa_speed * 0.06


def cpr_to_smm(cpr: float) -> float:
    """Convert annual CPR to Single Monthly Mortality."""
    return 1 - (1 - cpr) ** (1 / 12)
