# Explicit joint multiplication operators restore exponential width

Let (A) be a finite graded norm-convolution quotient. Choose (k) linear
forms in (A), and regard (A) as a graded module over

\[
 R=\mathbb F_p[T_1,\ldots,T_k]
\]

by sending (T_i) to multiplication by the corresponding form. For any
finite graded free (R)-resolution with Betti numbers (\beta_{i,j}),

\[
 (1-t)^kH_A(t)
   =\sum_j\left(\sum_i(-1)^i\beta_{i,j}\right)t^j.
\]

Consequently the absolute value of each numerator coefficient lower-bounds
the number of free summands in that shift, and the coefficient
(\ell_1)-norm lower-bounds the total number of summands. This is independent
of the chosen linear forms and survives all cancellations between adjacent
homological degrees.

For the exact dimension-ten quotient, the total-summand bounds as the number
of joint operators increases are

\[
 307,242,292,382,578,1068,1908,3450,6500,12834,25028
\]

for (k=0,1,\ldots,10). Thus the regime required by the generic-section
control---nine or ten independent operators---already restores nearly the
full explicit-resolution width.

## Semi-regular scaling model

The normalized base-two logarithms of the total-summand bounds are:

| (r) | (k=0) | (k=r/4) | (k=r/2) | (k=3r/4) | (k=7r/8) | (k=r) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 0.8997 | 1.0220 | 1.2719 | 1.5219 | 1.6469 | 1.7719 |
| 64 | 0.9356 | 1.1011 | 1.3511 | 1.6011 | 1.7261 | 1.8511 |
| 128 | 0.9603 | 1.1544 | 1.4044 | 1.6544 | 1.7794 | 1.9044 |
| 256 | 0.9763 | 1.1982 | 1.4482 | 1.6982 | 1.8232 | 1.9482 |

With only (\lfloor\sqrt r\rfloor) directions left outside the operator
algebra, the corresponding values are 1.6157, 1.7261, 1.8184, and 1.8857.
They trend toward the same (4^r) explicit scale as the full resolution.
The subexponential module-generator count from generic linear sections
therefore does not yield a small explicit joint-operator presentation.

## Exact limit

The Hilbert-numerator inequality is unconditional for explicit graded free
resolutions. The finite rows use exact measured Hilbert functions. The larger
rows are a semi-regular model, not an asymptotic theorem for norm ideals. The
bound counts explicit free summands; it does not exclude a circuit that
applies all differentials without listing them, an oracle for joint reduction,
or a non-resolution algorithm. No DLP exponent improvement is claimed.
