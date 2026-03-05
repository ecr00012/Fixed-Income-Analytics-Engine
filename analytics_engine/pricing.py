from analytics_engine.models import BondSpec, BondResult
from analytics_engine.solver import solve_ytm
from analytics_engine.mbs import price_mbs


def analyze_bond(spec: BondSpec) -> BondResult:
    """Compute analytics for a single bond, routing MBS to dedicated pricer."""
    if spec.bond_type and "mbs" in spec.bond_type.lower():
        return price_mbs(spec)
    return solve_ytm(spec)


def analyze_portfolio(specs: list[BondSpec]) -> list[BondResult]:
    """Analyze a list of bonds, returning a result for each."""
    return [analyze_bond(spec) for spec in specs]
