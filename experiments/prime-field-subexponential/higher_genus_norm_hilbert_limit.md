# Fixed higher genus does not collapse the homogeneous norm quotient

For a full-degree genus-$g$ Mumford target, a projective section space of
dimension $r$ has

\[
 \deg B\le\left\lfloor\frac{r-1}{2}\right\rfloor,
 \qquad
 \deg C\le\left\lfloor\frac r2\right\rfloor,
\]

and norm

\[
 wB^2-2vBC-uC^2.
\]

After fixing the top section coefficient, its nonleading coefficients give
$r+g$ homogeneous quadrics in $r$ variables. The control samples two valid
squarefree curves at each of the primes 101 and 103 for every genus 3 through
7. It computes all exact Hilbert profiles for $r=3,\ldots,8$, giving 120
sample computations aggregated into 30 genus/dimension panels.

Every four-sample profile is stable, and every measured coefficient is at
least the corresponding coefficient of the truncated semi-regular model

\[
 \left[\frac{(1-t^2)^{r+g}}{(1-t)^r}\right]_+.
\]

The norm structure often enlarges the terminal layers rather than producing
an early collapse. Representative profiles at $r=8$ are:

| genus | measured profile | semi-regular profile |
| ---: | --- | --- |
| 3 | 1, 8, 25, 32, 5, 0 | 1, 8, 25, 32, 0 |
| 4 | 1, 8, 24, 24, 2, 0 | 1, 8, 24, 24, 0 |
| 5 | 1, 8, 23, 20, 0 | 1, 8, 23, 16, 0 |
| 6 | 1, 8, 22, 16, 0 | 1, 8, 22, 8, 0 |
| 7 | 1, 8, 21, 12, 0 | 1, 8, 21, 0 |

For orientation, the semi-regular model's normalized base-two logarithm of
quotient length at $r=32,64,128,256$ is:

| genus | 32 | 64 | 128 | 256 |
| ---: | ---: | ---: | ---: | ---: |
| 2 | 0.8997 | 0.9356 | 0.9603 | 0.9763 |
| 3 | 0.8670 | 0.9120 | 0.9447 | 0.9667 |
| 4 | 0.8378 | 0.8910 | 0.9308 | 0.9578 |
| 5 | 0.8103 | 0.8717 | 0.9178 | 0.9495 |
| 6 | 0.7904 | 0.8545 | 0.9057 | 0.9416 |
| 7 | 0.7681 | 0.8382 | 0.8941 | 0.9341 |

Thus the extra $g-2$ equations improve finite-size constants, but for every
fixed tested genus the model still trends toward one bit of quotient length
per section variable. Since $r=\Theta_g(\log p)$ at binary-fiber occupancy,
this remains a positive power of $p$, not $p^{o(1)}$.

## Exact limit

The 120 sample profiles are exact finite-field computations on valid squarefree
curves. The larger dimensions are only a semi-regular model; the table is not
an asymptotic Hilbert-series theorem for the structured norm ideals. These
measurements exclude neither an implicit solver nor genus-dependent
correlations outside the homogeneous leading ideal. No DLP exponent
improvement is claimed.
