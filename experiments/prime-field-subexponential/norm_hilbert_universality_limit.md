# Universality control for the norm Hilbert tail

The curve-derived homogeneous norm ideals have a parity-dependent terminal
pattern: the measured odd-dimensional terminal component has dimension one,
while the even-dimensional values through section dimension ten are

\[
  2,4,8,16,32.
\]

This control tests whether the pattern is tied to the particular curve and
target divisors or to the convolutional norm form itself. For section
dimension $r$, it directly builds the coefficient quadrics of

\[
  wB^2-2vBC-uC^2
\]

with the same degree bounds as the chart at infinity. It samples four
independent triples $(u,v,w)$ in every dimension $3\le r\le8$ over each of
$\mathbb F_{101}$, $\mathbb F_{103}$, and $\mathbb F_{107}$. It also checks
the sparse deterministic triple

\[
  u=1+x^2,\qquad v=1+x,\qquad w=1+x^3.
\]

All 72 random profiles and all 18 deterministic profiles exactly match the
corresponding curve-derived profile. In particular, every even control ends
in dimension $2^{r/2}$ and every odd control ends in dimension one.

## Exact limit

This is finite evidence across three small prime fields and dimensions at most
eight, not a proof of a general Hilbert-series formula. It shows that the
observed tail is stable under independent coefficient changes and does not
require the original curve or planted target. The tail enlarges the quotient;
it does not remove the exponential middle layer or improve the DLP exponent.
An asymptotic result would need an explicit resolution or inverse-system
description of these convolutional quadrics.
