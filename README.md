# Project Overview

The Yield to Maturity (YTM) represents the expected annual rate of return earned on a bond under the assumption it is held until maturity.

From the perspective of a bond investor, the YTM is the anticipated total return received if the bond is held to its maturity date and all coupon payments are made on time and are then reinvested at the same interest rate.  

The hybrid Newton-Raphson x Bisection method for root finding is used to solve for YTM. The method alternates between Newton-Raphson and Bisection steps based on the following criteria:
```
if newton_step is inside bracket:
    accept newton step
else:
    take bisection step (midpoint of bracket)
```

## Solution

| Bond | Accrued Interest | Dirty Price | YTM (%) | CFY (%) | PSA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| B1: UST | 0.7212 | 98.9712 | 3.8119% | # | # |
| B2: IG Corp | 0.0000 | 101.4000 | 4.8106% | # | # |
| B3: HY Corp | 2.3111 | 94.4111 | 11.4601% | # | # |
| B4: MBS | 0.1750 | 99.1750 | 4.6225% | 4.7148% | 274.71 |
| B5: Zero Coupon | 0.0000 | 95.0000 | 5.2632% | # | # |


## Algorithm 
1. Find a bracket (range of initial guesses for the root)
2. Use the Newton-Raphson method to find the root 
3. If Newton tries something unsafe (e.g. the new guess is outside the bracket or the function diverges) , fall back to bisection (evaluating the function at the midpoint of the bracket), narrowing the range by two, ensuring the root is within the new range
4. Result returned when current guess is within 1e-10 of the true value or max iterations (100) is reached

    *Exception: Zero bonds are solved using a closed-form solution*

## Why bisection?
Newton-Raphson is faster than bisection, but can be unpredictable if the initial guess is not close to the root. Newton-Raphson can also fail in other scenarios, such as when the function is not differentiable at the root. Bisection is slower, but it is guaranteed to converge if the root is within the initial bracket.  

# Reasoning
The problem definition and provided data present a number of ambiguities that needed to be reasoned through and assumed before a robust solution could be implemented. These assumptions are documented below.

## Date of last payment
To calculate accrued interest, it is first required to determine the date of last payment.  
It is a standard assumption in fixed income that the date of last payment is the same as the day of maturity for corporate bonds and the 1st of the month for government bonds, as according to Fannie Mae/Freddie Mac conventions.   

## Face Value
It is assumed that the face value of all bonds is 100, according to bond price convention and that the dirty price is quoted as a percentage of face value.

## MBS Pricing
The main complication of the problem was the MBS bond. 
For the treasury, zero coupon, and corporate bonds, the maturity date is the guaranteed date of payment of principal.  
For an MBS, the WAL duration is not the guaranteed date of payment of principal, but rather the weighted average time to return of principal payment.

Because an MBS distributes principal payments as well as interest over time, YTM is not the most appropriate measure of return. For the purposes of calculating YTM, it is assumed that the date of settlement + the WAL is used as the date of maturity.

However, to determine a truer return of the MBS, I implemented a Cash Flow Yield (CFY) calculation. This calculates the rate of return based on the actual, amortizing cash flows of the mortgage pool.
To determine the values of the cash flows, the engine utilizes the standard Public Securities Association (PSA) prepayment model. Since the problem provided a fixed WAL, I use a root-finding algorithm (brentq, imported from scipy) to solve for the PSA speed that corresponds to the provided WAL.

The YTM solver uses an initial bracket of [−5%, 200%] to cover all realistic fixed income scenarios, including deeply distressed bonds, while guaranteeing the pricing function changes sign across the interval.

# Recommendations and Future Work
The current project architecture is intentionally modular and robust, promoting scalability. To improve the usability of the income analytics engine, I would recommend moving the input logic to an asynchronous API. 

I would also recommend adding support for other metrics, such as modified duration to provide investors with a measure of price sensitivity to interest rate changes.

I would also recommend adding support for other bond types, such as floating rate notes-by adding logic to support variable coupon payments-and inflation linked bonds-by adjusting the principal amount based on the Consumer Price Index.

# Environment and Technical Specifications

## Environment
This project is built with uv.
run 'uv sync' to install dependencies.  

## Python Version
- Python 3.11

## Dependencies
* pytest
* scipy
* python-dateutil