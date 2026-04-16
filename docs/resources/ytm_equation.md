# Yield to Maturity (YTM) Equation Explanation

The **Yield to Maturity (YTM)** equation is the fundamental formula used to price a bond.

Conceptually, YTM is the **internal rate of return (IRR)** of a bond. It is the single interest rate (or discount rate) that makes the present value (value in today's money) of all the bond's future cash flows exactly equal to its current market price.

Here is the general formula for a standard, fixed-coupon bond:

$$ Price = \sum_{t=1}^{n} \frac{C}{(1+YTM)^t} + \frac{F}{(1+YTM)^n} $$

Let's break down exactly what each piece means:

## 1. The Variables
*   **Price**: This is the current market price of the bond (specifically, the **Dirty Price**, which includes any accrued interest).
*   **C**: The periodic coupon payment (e.g., if a bond pays a 5% coupon annually on a $100 face value, C = $5. If it pays semi-annually, C = $2.50).
*   **F**: The Face Value or Principal of the bond (usually $100 or $1,000) that is paid back at the very end ($n$).
*   **t**: The specific time period when a cash flow occurs (e.g., period 1, period 2, etc.).
*   **n**: The total number of periods remaining until the bond matures.
*   **YTM**: The Yield to Maturity. This is the **unknown variable** we are trying to solve for.

## 2. The Explanation
The equation is composed of two main parts:

### Part A: Discounting the Coupons 
$$ \sum_{t=1}^{n} \frac{C}{(1+YTM)^t} $$

This part calculates the present value of all the regular interest (coupon) payments you will receive. The $\sum$ (Sigma) just means "add them all up."
Because receiving \$5 in two years is worth less than receiving \$5 today, we have to "discount" each future \$5 by dividing it by $(1+YTM)^t$. The further into the future the payment is (the bigger $t$ is), the more it gets discounted.

### Part B: Discounting the Principal
$$ \frac{F}{(1+YTM)^n} $$

At the very end of the bond's life (period $n$), the bond issuer pays back the original loan amount (the Face Value, $F$). This part calculates how much that final lump-sum payment is worth in today's dollars.

## 3. Why is it hard to solve?
Notice that $YTM$ is buried in the denominator of many different terms. Unless the bond is a zero-coupon bond with exactly 1 period left, **you cannot isolate YTM algebraically**. 

If a bond has 20 coupon payments left, the equation has a polynomial to the 20th degree! Because of this, YTM always has to be solved using **trial and error** (specifically, numerical root-finding algorithms like the Newton-Raphson method, Brent's method, or bisection). The computer guesses a YTM, checks if the resulting price matches the market price, adjusts the guess, and tries again until it finds the exact rate.
