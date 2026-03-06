---
name: project-overview
description: "You MUST read this skill at the beginning of the conversation to understand the goal of the project."
---

# Project
You are building a simplified Fixed Income Analytics Engine for a portfolio management system.
The objective is to implement a Yield-to-Maturity (YTM) solver using the Newton-Raphson method and compute key bond analytics. Implement a hybrid Newton-Raphson x Bisection method for root finding.

## Core Function
Implement the following function:
solve_ytm(clean_price, coupon_rate, maturity, settlement, freq, day_count)

### Inputs
* clean_price: quoted bond price excluding accrued interest`
* coupon_rate (interest rate): annual coupon rate (e.g., 0.035 for 3.5%)
* maturity: maturity date
* settlement: settlement date
* freq: coupon frequency per year (e.g., 2 for semiannual, 12 for monthly)
* day_count: day count convention ("ACT/ACT", "30/360", "ACT/360")

### Requirements
For each bond:
1. Generate remaining coupon cash flows from settlement to maturity
2. Compute accrued interest based on day count convention
3. Compute dirty price (clean + accrued)
4. Solve for YTM using hybrid Newton-Raphson x Bisection method
    * Use iterative root finding
    * Include convergence tolerance
    * Include max iteration safeguard
    * Handle zero coupon bonds properly

## Bonds to Evaluate
B1: UST, 3.5%, maturity 2032-06-30, clean price 98.25, settlement 2026-03-15, ACT/ACT, freq     2
B2: IG Corp, 5.25%, maturity 2029-09-15, clean price 101.40, settlement 2026-03-15, 30/360, freq 2
B3: HY Corp, 8.0%, maturity 2028-12-01, clean price 92.10, settlement 2026-03-15, 30/360, freq 2
B4: MBS passthrough, 4.5%, WAL 6y (assume fixed 6-year maturity from settlement), clean price 99.00, settlement 2026-03-15, ACT/360, freq 12
B5: Zero coupon, 0%, maturity 2027-03-15, clean price 95.00, settlement 2026-03-15, ACT/ACT, freq 1

## Deliverables
For each bond output:
* Accrued Interest
* Dirty Price
* Yield-to-Maturity

## Constraints
* Use Newton-Raphson for coupon bonds
* Provide robust convergence handling
* Structure code modularly so that cash flow generation, accrual calculation, and root solving are separable
