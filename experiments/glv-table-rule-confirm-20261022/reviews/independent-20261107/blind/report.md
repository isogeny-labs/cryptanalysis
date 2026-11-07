# Blind arithmetic review: GLV table rule

Source: only the definitions and targets in the assigned prompt. No implementation, proof, receipt, history, or sibling material was consulted.

Let `r0 = 8` and `r(n+1) = step(b,r(n))`. Direct substitution gives:

| Budget `b` | `r0` | `r1` | `r2` | `r3` | `tableSize(b)` |
|---|---:|---:|---:|---:|---:|
| `b < 16` | 8 | 8 | 8 | 8 | 8 |
| `16 <= b < 32` | 8 | 16 | 16 | 16 | 16 |
| `b >= 32` | 8 | 16 | 32 | 32 | 32 |

Thus the loop reaches `tableSize(b)` after at most two applications of `step`; a third application is fixed. It terminates after zero, one, or two changing steps. The cases also prove that `tableSize` is nondecreasing in `b`.

For natural `s` and `lg > 0`, both denominators are positive and `48*lg >= 12*lg`. Division of the same nonnegative numerator by the larger positive denominator cannot increase the floor quotient, so `b48 <= b12`. Monotonicity then gives `tableSize(b48) <= tableSize(b12)`, and the loop result has the same ordering.

Boundary controls: `b=15 -> 8`, `b=16 -> 16`, `b=31 -> 16`, `b=32 -> 32`. For `s=0` and `lg>0`, both budgets are zero and both loop results are 8. For `s=384, lg=1`, `b48=8` and `b12=32`, giving loop results 8 and 32 respectively.

The premise `lg>0` is needed for ordinary quotient reasoning. At `lg=0`, both denominators are zero, so the mathematical floor quotients are undefined. A totalized natural-number division operation may still assign values there; that convention cannot be used as evidence for the positive-denominator argument.

A nearby strict claim is false: `tableSize` is not strictly increasing (`b=16` and `b=17` both give 16), and `tableSize(b48) < tableSize(b12)` fails for `s=0`. The ordering alone implies no runtime or other performance comparison.

**Disposition:** all requested non-strict arithmetic claims hold under the stated natural-number premises; the nearby strict claims break. No implementation or Lean-proof fidelity conclusion is made from this blind review.
