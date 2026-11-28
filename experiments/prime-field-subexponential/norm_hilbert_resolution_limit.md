# Hilbert-numerator boundary for explicit norm resolutions

Let $S=\mathbb F_p[z_1,\ldots,z_r]$ and let $A=S/I$ be one of the homogeneous
norm-convolution quotients. If

\[
  0\leftarrow A\leftarrow
  \bigoplus_{i,j} S(-j)^{\beta_{i,j}}
\]

is a graded free resolution, then its Hilbert numerator is

\[
  K_A(t)=(1-t)^rH_A(t)
        =\sum_j\left(\sum_i(-1)^i\beta_{i,j}\right)t^j.
\]

Consequently, for every shift $j$,

\[
  \sum_i\beta_{i,j}\ge |[t^j]K_A(t)|,
\]

and the total number of free summands is at least the coefficient
$\ell_1$-norm of $K_A$. This remains true after every possible cancellation
between adjacent homological degrees.

The exact controls give the following lower bounds:

| section dimension | one-shift bound | total-summand bound |
| ---: | ---: | ---: |
| 3 | 5 | 12 |
| 4 | 12 | 36 |
| 5 | 46 | 114 |
| 6 | 56 | 198 |
| 7 | 349 | 1,000 |
| 8 | 664 | 1,890 |
| 9 | 2,415 | 8,274 |
| 10 | 7,492 | 25,028 |

Thus the measured structured Hilbert tails do not come from narrow explicit
free resolutions. For orientation, the semi-regular model at
$r=8,16,32,64,128$ has

\[
  \frac1r\log_2\max_j|[t^j]K_A|
  =1.1865,1.4774,1.6849,1.7995,1.8747,
\]

while the normalized logarithm of the coefficient $\ell_1$-norm is
$1.3769,1.6121,1.7719,1.8511,1.9044$. These model values trend toward an
explicit resolution scale near $4^r$, not a subexponential state space.

## Exact limit

The inequalities for the measured panels are rigorous consequences of their
exact Hilbert functions. The larger-dimension rows are only semi-regular model
values; they are not an asymptotic theorem for norm ideals. The bound concerns
an explicit list of free summands. It does not exclude a succinct patterned
complex, an oracle for its differentials, or an elimination algorithm that
never materializes the resolution. No DLP exponent improvement is claimed.
