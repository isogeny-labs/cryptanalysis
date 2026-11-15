# Independent blind algebra review: Hecke 432 dual equation

## Input and method

I used only the supplied `blind-input.md`. Write $t=X^3$. The calculations below are polynomial identities over ℤ, so the first identity remains valid after substitution into any commutative ring. Division in the second calculation takes place in a field with $X\ne0$.

## Polynomial statement: holds

Direct expansion gives

\[
(t-16)(t+128)^2=t^3+240t^2+12288t-262144,
\]
\[
(t-64)^3=t^3-192t^2+12288t-262144.
\]

Their difference is $432t^2=432X^6$. No field assumption or source-curve equation is used here.

## Rational statement: holds on $X\ne0$ with the source equation

Set $x'=(X^3-64)/X^2$ and $y'=Y(X^3+128)/X^3$. Because $X\ne0$, $X^6=t^2$ is invertible. If $Y^2=t-16$, then

\[
(y')^2-(x')^3
=\frac{Y^2(t+128)^2-(t-64)^3}{t^2}
=\frac{(t-16)(t+128)^2-(t-64)^3}{t^2}
=432.
\]

Thus the displayed formulas send every source-curve point with $X\ne0$ to a point satisfying $y'^2=x'^3+432$.

## Nearby false controls

1. **Change 128 to 127.** The exact polynomial residual is

   \[
   (t-16)(t+127)^2-(t-64)^3-432t^2
   =-2t^2-223t+4080.
   \]

   At $X=1$, use the field $\mathbb Q(\sqrt{-15})$ and $Y=\sqrt{-15}$, so $Y^2=X^3-16=-15$. The modified output is $x'=-63$, $y'=128Y$. Its target-equation residual is
   \[
   (y')^2-(x')^3-432
   =-245760+250047-432=3855\ne0.
   \]
   This is a source point with a defined modified formula, not just a symbolic failure.

2. **Omit $Y^2=X^3-16$.** For arbitrary $Y$ and $X\ne0$, the exact residual is

   \[
   (y')^2-(x')^3-432
   =\frac{\bigl(Y^2-(X^3-16)\bigr)(X^3+128)^2}{X^6}.
   \]

   In $\mathbb Q$ take $X=4,Y=0$.  The formulas give $x'=0,y'=0$, while the target equation requires $0=432$. The omitted source condition would have required $Y^2=48$.

3. **Set $X=0$.** The polynomial statement still reads
   \((-16)128^2-(-64)^3=0\), so it holds. The rational formulas have denominators $X^2$ and $X^3$ and are undefined there. For an actual source-curve point, take $X=0,Y=4i$ over $\mathbb C$; then $Y^2=-16$, but neither displayed rational coordinate has a value. Cross-multiplication does not assign a target point.

## Scope of the result

The equations give a rational coordinate map on the affine open locus $X\ne0$, and an exact identity for its image. They alone do not supply values at $X=0$ or the projective point at infinity, prove that a global extension is a group homomorphism, establish its degree, or prove a modular-polynomial identity. Those assertions require separate geometric or modular arguments. In characteristics 2 and 3, the displayed Weierstrass equations are singular, so even calling them elliptic curves requires a characteristic restriction.
