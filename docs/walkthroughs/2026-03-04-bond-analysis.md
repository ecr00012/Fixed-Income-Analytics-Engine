# Bond Analysis: CLI Output Results

This document provides an analysis of the results produced by the Fixed Income Analytics Engine CLI for each of the 5 target bonds.

## Overview of Bond Math Principles
Before looking at the individual bonds, it's helpful to remember the core relationship in fixed income: **price and yield move inversely**.
*   **Par Bond:** When a bond is priced exactly at its face value (100), its Yield-to-Maturity (YTM) equals its stated coupon rate.
*   **Discount Bond:** When a bond is priced below 100, an investor is buying it "on sale." They will receive the face value at maturity, meaning their total return (YTM) will be **higher** than the stated coupon rate.
*   **Premium Bond:** When a bond is priced above 100, an investor is paying extra. Even though they receive the stated coupon payments, they will suffer a capital loss at maturity when they only receive 100. Thus, their total return (YTM) will be **lower** than the stated coupon rate.

## CLI Output Reference

```text
Bond                 |   Accrued Interest |   Dirty Price |    YTM (%)
----------------------------------------------------------------------
B1: UST              |             0.7212 |       98.9712 |    3.8119%
B2: IG Corp          |             0.0000 |      101.4000 |    4.8106%
B3: HY Corp          |             2.3111 |       94.4111 |   11.4601%
B4: MBS              |             0.0000 |       99.0000 |    4.6225%
B5: Zero Coupon      |             0.0000 |       95.0000 |    5.2632%
```

---

## Individual Bond Analysis

### B1: US Treasury (UST)
*   **Properties:** 3.5% coupon, semi-annual (`freq=2`), matures June 2032, `ACT/ACT` convention. Clean Price = 98.25. Settlement = March 15, 2026.
*   **Accrued Interest (0.7212):** The previous coupon payment was on December 30, 2025. Between December 30 and March 15 (settlement), 75 actual days have elapsed in the current 182-day coupon period. The accrued interest is the pro-rata share of the 1.75% semi-annual coupon: `1.75 * (75/182) ≈ 0.721`.
*   **Dirty Price (98.9712):** The clean price (98.25) plus the accrued interest owed to the seller.
*   **YTM (3.8119%):** Because the bond is priced at a discount (98.25 < 100), the investor gets the 3.5% coupon *plus* a capital gain as the bond pulls to par (100) at maturity. Therefore, the YTM (3.81%) is higher than the coupon rate (3.5%).

### B2: Investment Grade Corporate (IG Corp)
*   **Properties:** 5.25% coupon, semi-annual (`freq=2`), matures Sept 2029, `30/360` convention. Clean Price = 101.40. Settlement = March 15, 2026.
*   **Accrued Interest (0.0000):** The bond pays coupons every March 15 and September 15. Because the settlement date falls *exactly* on a coupon payment date, the seller keeps the coupon paid that day, a new period begins, and no interest has accrued for the next period yet.
*   **Dirty Price (101.4000):** Equal to the clean price since accrued interest is zero.
*   **YTM (4.8106%):** This bond is trading at a premium (101.40 > 100). The investor is locking in a 5.25% cash flow, but they will lose 1.40 points of principal by maturity. This capital loss offsets some of the coupon income, dragging the total yield down to 4.81% (lower than the 5.25% coupon).

### B3: High Yield Corporate (HY Corp)
*   **Properties:** 8.0% coupon, semi-annual (`freq=2`), matures Dec 2028, `30/360` convention. Clean Price = 92.10. Settlement = March 15, 2026.
*   **Accrued Interest (2.3111):** Coupons are paid on June 1 and December 1. The previous coupon was December 1, 2025. Under `30/360`, there are exactly 104 days between Dec 1 and March 15. The semi-annual coupon is 4.0. `4.0 * (104 / 180) ≈ 2.311`.
*   **Dirty Price (94.4111):** Clean price (92.10) + accrued interest (2.3111).
*   **YTM (11.4601%):** This "junk" bond is deeply discounted (92.10). The investor gets a high 8.0% running yield *and* locked-in capital appreciation of 7.9 points over an aggressive timeframe (less than 3 years). This combination of high coupon and steep discount results in a double-digit YTM of 11.46%.

### B4: Mortgage-Backed Security Passthrough (MBS)
*   **Properties:** 4.5% coupon, monthly (`freq=12`), assumed 6-year maturity (March 30, 2032), `ACT/360` convention. Clean Price = 99.00. Settlement = March 15, 2026.
*   **Accrued Interest (0.0000):** Since coupons are paid monthly, they occur on the 15th of every month. The settlement date is exactly on a coupon date, resulting in zero accrued interest.
*   **Dirty Price (99.0000):** Equal to the clean price.
*   **YTM (4.6225%):** The bond is trading at a slight discount (99.00 < 100), meaning the YTM must be slightly higher than the 4.5% coupon. A key factor here is the monthly compounding (`freq=12`). Receiving cash flows 12 times a year allows for faster reinvestment, which slightly boosts the annualized yield compared to a semi-annual bond with identical specs.

### B5: Zero Coupon Bond
*   **Properties:** 0% coupon, matures March 15, 2027 (exactly 1 year from settlement). `ACT/ACT` convention. Clean Price = 95.00. Settlement = March 15, 2026.
*   **Accrued Interest (0.0000):** Zero coupon bonds do not pay periodic interest, so there is nothing to accrue.
*   **Dirty Price (95.0000):** Equal to the clean price.
*   **YTM (5.2632%):** Unlike the others, our engine calculates this using a closed-form solution: `(Face / Price)^(1/Years) - 1`. Here, the investor pays 95 today and receives 100 in exactly one year. `(100 / 95)^1 - 1 = 0.05263`, or exactly 5.2632%. All of the return comes purely from capital appreciation.

---

## FAQ: Concepts

### What are "Coupons"?
In fixed income, a **coupon** is simply the regular interest payment that the bond issuer pays to the bondholder. 

The term comes from historical practice: physical paper bonds used to have small detachable "coupons" printed around the edges. When an interest payment was due, the investor would literally cut off the appropriate coupon with scissors and hand it to a bank to receive their cash. 

### Why do some bonds have $0 Accrued Interest?
The term "accrued interest" sounds like "total money earned," but in the bond market, it is a specific mechanical "truing up" between buyers and sellers.

If a bond pays a $6 coupon every 6 months (June 1 and Dec 1), and you buy it from me exactly halfway through the period (March 1), it isn't fair that you get the *entire* $6 coupon on June 1 when I held the bond for the first 3 months. To make it fair, when you buy the bond on March 1, you must pay me the market value of the bond (Clean Price) **PLUS the Accrued Interest** (the $3 I earned but haven't been paid yet). 

However, if you buy the bond from me on the exact day the coupon is paid (e.g., Dec 1), I just keep the coupon the issuer hands me. You start fresh for the next period, so you owe me $0 in accrued interest. **This is why Bonds 2 and 4 had $0 accrued interest — the settlement date fell exactly on a coupon payment date.**

### If accrued interest is $0, is the total return $0?
No! It helps to separate the concept of **Accrued Interest** (the mechanical daily payment to a seller) from **Total Return or Yield** (the actual money you make).

The **Yield to Maturity (YTM)** represents the *actual, total annualized return* you get from holding the bond. It consists of two things combined:
1.  The coupon payments you collect along the way.
2.  The capital gain (or loss) between the price you paid and the $100 you get back at maturity.

For the **Zero Coupon Bond (B5)**, there are no coupons to fight over with a seller, so the "accrued interest" trading mechanism is always $0. But the total return is emphatically *not* zero: you pay $95 today, and you get $100 in a year. That $5 profit is a very real **5.26% YTM**, even though the "accrued interest" line item on the trade ticket says $0.00.

### Should Yield to Maturity be a Percentage or an Amount?
Yield to Maturity is **always expressed as an annualized percentage rate**, never as a currency amount.

- **Accrued Interest and Dirty Price** are currency amounts (e.g., $0.72 or $98.97 per $100 of face value). They tell you exactly how much money changes hands on the settlement date.
- **YTM** is a rate of return (e.g., 3.81%). It acts as the "internal rate of return" (IRR) that equates the present value of all future cash flows to the bond's current dirty price. 

Expressing yield as a percentage allows investors to universally compare the return of bonds with completely different prices, maturities, and coupon rates on an apples-to-apples basis.
