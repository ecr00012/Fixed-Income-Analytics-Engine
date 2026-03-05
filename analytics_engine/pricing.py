from analytics_engine.models import BondSpec, BondResult
from analytics_engine.solver import solve_ytm


def analyze_bond(spec: BondSpec) -> BondResult:
    """Compute accrued interest, dirty price, and YTM for a single bond."""
    return solve_ytm(spec)


def analyze_portfolio(specs: list[BondSpec]) -> list[BondResult]:
    """Analyze a list of bonds, returning a result for each."""
    return [analyze_bond(spec) for spec in specs]
