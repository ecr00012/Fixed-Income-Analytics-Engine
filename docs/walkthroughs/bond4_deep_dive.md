# Bond 4 — MBS Passthrough Deep Dive

## What makes B4 structurally different

Every other bond in the table has a fixed, known cash flow schedule. You know exactly when coupons arrive and when principal returns. B4 is a **mortgage-backed passthrough**, which means it represents a pool of individual homeowner mortgages. Each month, borrowers make payments that blend interest *and* principal repayment together — and that combined payment gets "passed through" to the bondholder. This creates three fundamental differences:

- Cash flows are **monthly**, not semi-annual or annual
- Principal returns **gradually** throughout the life of the bond, not in a lump sum at maturity
- There is **no fixed maturity date** — borrowers can prepay at any time

---

## What WAL means and why it's used

Because there's no single maturity date, MBS analysis substitutes **Weighted Average Life (WAL)** — the average time until each dollar of principal is returned, weighted by how much principal is returned at each point. A WAL of 6 years means the *average* dollar of principal comes back in year 6, even though some comes back in month 1 and some potentially in year 20+.

The critical thing to understand: **WAL is not maturity**. It's a summary statistic that compresses a complex principal distribution into a single number. Using it as if the bond were a 6-year bullet (all principal returned at year 6) is a deliberate simplification.

---

## The accrued interest calculation

B4 uses **ACT/360** day count, which is standard for MBS and most money-market instruments. The logic:

1. Identify the most recent coupon date — taken as **February 1, 2026**
2. Count actual calendar days from Feb 1 to the March 15 settlement: **42 days**
3. The annual coupon is 4.5%, so the monthly coupon on $100 face is $0.375
4. Accrued interest = `4.5% × 100 × (42/360)` = **$0.525**

ACT/360 slightly *overstates* accrual relative to ACT/365, because you're dividing by a shorter year. This is intentional in the convention — it effectively gives the seller a marginally higher accrued interest amount.

---

## The YTM calculation and its assumptions

YTM here is computed as a **monthly IRR annualized by multiplying by 12** (bond-equivalent yield). The process:

1. Model the bond as paying a **fixed monthly coupon** of `4.5%/12 × 100 = $0.375` for 72 months (6y WAL)
2. Assume **all remaining principal ($100) returns at month 72** as a bullet payment
3. Solve for the monthly discount rate that makes the PV of all those cash flows equal to the **dirty price of $99.525**
4. Multiply that monthly rate by 12 to get the annualized YTM of ~**4.59%**

---

## Where the ambiguity lives

This is where B4 diverges sharply from the clean analytics of the other bonds.

**1. The WAL assumption is a fiction**
Real MBS cash flows depend on prepayment behavior. The industry standard is to model this using **PSA prepayment speeds** (e.g., "100 PSA" or "200 PSA"). A faster prepayment speed shortens effective duration and changes YTM materially. The 6-year WAL given here implicitly assumes *some* prepayment model, but we don't know which one — and changing the assumption can move YTM by tens of basis points or more.

**2. Bullet vs. scheduled amortization**
In reality, principal doesn't all return at the WAL date — it trickles in every month. The calculation here treats it as a bullet, which misrepresents the actual cash flow timing. A proper treatment would schedule monthly principal payments (scheduled amortization + prepayments) and discount each one individually. The bullet simplification is a common approximation but introduces pricing error.

**3. ACT/360 vs. ACT/365 convention**
MBS typically uses ACT/360 for accrual, but some agency securities (Fannie, Freddie, Ginnie) use slightly different accrual conventions or settle on different cycles. The February 1 coupon date assumed here is a convention choice — MBS typically pay on the **25th of each month** with a delay, or on the 1st depending on the agency. The exact previous coupon date isn't stated in the problem, creating a genuine ambiguity.

**4. Annualization method**
Multiplying the monthly IRR by 12 gives a **nominal annual rate**, not an effective annual rate. The EAR would be `(1 + monthly rate)^12 − 1`, which would be slightly higher. For comparison against semi-annual bonds (B1–B3), you'd want to convert carefully — the ~4.59% here is not directly comparable to the semi-annual YTMs without an adjustment.

**5. Yield spread context**
Unlike the other bonds, MBS YTM is rarely the primary metric practitioners care about. The more meaningful measure is **OAS (Option-Adjusted Spread)** — the spread over the risk-free rate after stripping out the value of the embedded prepayment option (the borrower's right to refinance). YTM on an MBS conflates the base rate, credit spread, and prepayment optionality into a single number, making it a blunt instrument.

---

## Bottom line

B4's YTM of ~4.59% is best understood as a *rough approximation* under a specific set of structural assumptions. It's directionally useful but should be treated with more skepticism than the YTMs on B1–B3, which are mathematically exact given their inputs. Any serious MBS analysis would require a full prepayment model, scheduled amortization cash flows, and OAS rather than nominal YTM.
