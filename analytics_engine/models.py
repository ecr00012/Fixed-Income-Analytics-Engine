from dataclasses import dataclass
from datetime import date


@dataclass
class BondSpec:
    name: str
    clean_price: float
    coupon_rate: float
    maturity: date
    settlement: date
    freq: int
    day_count: str


@dataclass
class BondResult:
    spec: BondSpec
    accrued_interest: float
    dirty_price: float
    ytm: float
