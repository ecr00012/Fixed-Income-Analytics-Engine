# Mortgage-Backed Securities (MBS) Pricing Explanation

Pricing a Mortgage-Backed Security (MBS) is fundamentally different—and significantly more complex—than pricing a standard fixed-coupon bond.

While standard bonds have a fixed maturity date and guaranteed semi-annual interest payments with a single massive principal repayment at the end, an MBS represents a pool of thousands of individual homeowner mortgages. Homeowners make **monthly payments** that include both interest *and* a portion of the principal. Furthermore, homeowners can sell their homes or refinance, paying off their entire mortgage early. This is called **prepayment risk**.

Because the principal amortizes (pays down) every month and is subject to unpredictable early prepayments, the cash flows of an MBS are unknown in advance. The core function of an MBS Pricer is to project these unknown cash flows using market models before it can solve for a yield or price.

Here is the general workflow used to price an MBS:

## 1. The Prepayment Model (PSA)
To project cash flows, the market must agree on an assumption about how fast homeowners will prepay their mortgages. The standard industry benchmark is the **Public Securities Association (PSA) Prepayment Model**.

*   **100% PSA** assumes that prepayment rates (CPR - Conditional Prepayment Rate) start at 0.2% in month 1, increase by 0.2% every month until month 30, and then plateau forever at 6.0% CPR.
*   **Faster Prepayments:** If interest rates drop (causing a wave of refinancing), the market might assume **200% PSA**, meaning prepayments arrive exactly twice as fast as the baseline curve.
*   The pricer dynamically converts this annualized CPR curve into a Single Monthly Mortality (SMM) rate to figure out exactly how much principal is prepaid *this specific month*.

## 2. Generating the Cash Flows
Once a PSA speed is assumed, the pricer runs a month-by-month simulation for the entire legal term of the pool (usually 360 months / 30 years). For each month, it calculates:

1.  **Scheduled Interest:** The current remaining pool balance × the monthly mortgage rate.
2.  **Scheduled Principal:** The standard amortization amount required to pay off the loan by month 360.
3.  **Prepayment:** The remaining balance multiplied by that month's specific SMM rate.

The Total Cash Flow for that month is the sum of these three components. Because of prepayments, the pool balance shrinks faster than a standard amortization schedule, meaning the cash flows eventually taper off mathematically to zero before the 360th month.

## 3. Weighted Average Life (WAL)
Because an MBS essentially "matures" continuously as principal is returned, measuring its length using the legal 30-year maturity date is meaningless to an investor. Instead, the market calculates the **Weighted Average Life (WAL)**. 

The WAL is the average time (in years) it takes for every dollar of principal to be returned to the investor. 
$$ WAL = \frac{\sum (Time_{months} \times Principal_{paid})}{\sum Principal_{paid}} \div 12 $$

If the market bids an MBS with a "6-Year WAL", the pricer's first job is a reverse root-finding operation: It must discover exactly which PSA speed generates cash flows that result in a mathematically perfect 6-year WAL.

## 4. Cash Flow Yield (CFY)
Once the exact month-by-month cash flows are generated based on the PSA speed, the pricer can finally calculate the yield. This internal rate of return is called the **Cash Flow Yield (CFY)**.

Because an MBS pays monthly, the solver first finds the *monthly* discount rate that makes the present value of the 360 monthly cash flows equal the current market price (Dirty Price). 

$$ Dirty Price = \sum_{t=1}^{360} \frac{Cash Flow_t}{(1+MonthlyYield)^t} $$

To make this yield comparable to standard semi-annual Treasury bonds, the monthly yield is compounded into a **Bond-Equivalent Yield (BEY)**:
$$ BEY = [(1 + MonthlyYield)^6 - 1] \times 2 $$

## Summary of the Pricing Pipeline
Unlike a standard `solve_ytm()` function, an `analyze_mbs()` function must run a complete multi-step pipeline:
1.  **Solve PSA from WAL:** Find the prepayment speed the market is implying.
2.  **Generate Cash Flows:** Simulate 30 years of monthly interest, amortization, and prepayments.
3.  **Solve CFY:** Find the discount rate that links those scheduled cash flows to the quoted market price.

## Why is CFY Higher?
The key insight is the timing of principal repayment. Under the PSA model at 274.71% PSA, homeowners are prepaying very aggressively — nearly 2.75x the baseline rate. This means the investor gets a large chunk of their principal back much earlier than the stated maturity.

When you receive more of your money back sooner, you need to re-invest it. This creates what's called reinvestment risk — but it also means the cash flows are "front-loaded." The CFY solver must find the rate that discounts those early, heavier cash flows back to today's price of 99.175.

Because the cash flows are concentrated earlier (rather than spread evenly to 2032), the effective discount rate needed to make them equal the current price is slightly higher. 

Under the CFY model, the 274% PSA means homeowners are prepaying aggressively — so you're receiving a large portion of your principal back in the early months, long before month 72.

In the YTM model, that same $100 stays locked up and only comes back as a single bullet at the end. Getting money back early is worth more (time value of money), so the IRR needed to make those early-returning cash flows discount down to today's price of 99.175 ends up being slightly higher than the YTM.

In short: same price, same 6-year life, but the CFY model's cash flows are front-loaded → higher implied return