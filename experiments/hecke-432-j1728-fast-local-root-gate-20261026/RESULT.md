# Fixed-degree polynomial gcd gate for exceptional C–E fibers

A finite-field polynomial gcd gate reproduces the exact C–E pair counts at **all eleven** global-norm exceptions below ten million. It processes the 22 rational source-`j=1728` C points with **501 polynomial multiplications and 811 polynomial remainders** in total; the largest individual E-fiber uses 48 polynomial multiplications. These are counted operations in the new fixed-degree E-fiber kernel. The prior direct checks of small exceptional cells scanned field values, while this kernel uses modular polynomial exponentiation whose multiplication count grows with `log p` for fixed resolvent degree. Source-point extraction is a separate degree-18 finite-field factorization step and is excluded from those kernel counts.

| Prime | Rational source C points | Rational `x_E` roots | Rational C–E pairs | Source-j map undefined on an additional C point |
| ---: | ---: | ---: | ---: | ---: |
| 11 | 2 | 2 | 2 | 1 |
| 131 | 2 | 4 | 4 | 0 |
| 179 | 2 | 1 | 0 | 0 |
| 227 | 2 | 1 | 2 | 0 |
| 251 | 2 | 1 | 0 | 0 |
| 419 | 2 | 1 | 0 | 0 |
| 491 | 2 | 1 | 0 | 0 |
| 1523 | 2 | 1 | 2 | 0 |
| 148139 | 2 | 1 | 2 | 0 |
| 182339 | 2 | 1 | 2 | 0 |
| 1237499 | 2 | 0 | 0 | 0 |
| **Total** | **22** | **14** | **14** | **1** |

[`protocol.json`](protocol.json) froze the eleven primes, exact source and resolvent hashes, and pair-count predictions from the earlier direct receipts before this implementation. [`run.py`](run.py) verifies those hashes, extracts rational source points from the original source-j map and degree-18 coordinate polynomial, then applies the gcd gate. Its complete per-source results and operation counts are in [`result.json`](result.json). [`validate.py`](validate.py) binds the result to the earlier direct receipts and the independent Sage replay; [`validation.json`](validation.json) reports `PASS_FAST_LOCAL_GCD_EVIDENCE`.

## Why the E-fiber gate counts points

Let `R(z)∈F_p[z]` be the specialized C–E resolvent at a fixed rational source point, with `p` odd. The polynomial `z^p−z` has each element of `F_p` as a simple root. Therefore `G=gcd(R,z^p−z)` is squarefree, and its degree is the number of distinct rational `x_E` roots of `R`. This step needs only `z^p mod R`, followed by a gcd; binary exponentiation uses `O(log p)` modular polynomial multiplications at the fixed degree `deg R≤12`.

Put `A(z)=z³+432`, `G₀=gcd(G,A)`, and `G₊=gcd(G,A^((p−1)/2)−1)`. Euler's criterion says `A(x)^((p−1)/2)=1` exactly when `A(x)` is a nonzero square. Each root of `G₀` has one E lift with `y_E=0`; each root of `G₊` has two lifts `±y_E`. Since both gcds divide squarefree `G`, the rational pair count is `deg G₀ + 2 deg G₊`. The implementation reduces the large power modulo `G` before its gcd, again using `O(log p)` fixed-degree polynomial multiplications. It retains `DEGENERATE_ZERO_RESOLVENT` explicitly if the specialized resolvent vanishes identically; none of the frozen cells took that path.

[`audit_protocol.json`](audit_protocol.json) pinned the first run before independent validation. [`audit_sage.py`](audit_sage.py) used the repository's checked Sage launcher to reconstruct every source point, solve each specialized resolvent using Sage's polynomial roots, test `x_E³+432` for squares, and compare the root and pair counts for all 22 fibers. [`audit.json`](audit.json) has status `PASS_INDEPENDENT_SAGE_FAST_LOCAL_GATE_REPLAY`; [`sage-runtime-info.txt`](sage-runtime-info.txt) records the accepted runtime. At `p=11`, one additional point of the reduced degree-18 source polynomial lies on C but makes the source-j map denominator zero, so it is explicitly excluded from the source-`j=1728` fiber.

## Proof map and accounting boundary

[`FrobeniusGcdGate.lean`](formal/FrobeniusGcdGate.lean) checks the structural statement that, whenever `q`-power Frobenius fixes every coefficient-field element, a point is a root of `gcd(R,X^q−X)` exactly when it is a root of `R`. The [Lean receipt](formal/lean-check.txt) pins the toolchain and mathlib revision; `#print axioms` lists only `propext`, `Classical.choice`, and `Quot.sound`. Its explicit Frobenius-fixed hypothesis is supplied by the finite-field law for these prime fields. The squarefree-degree counting step, Euler-criterion branch count, and the eleven concrete input arrays remain executable exact-arithmetic checks rather than Lean-encoded certificates, so full formalization is partial.

The 501 multiplications, 811 remainders, 44 gcds, 33 modular exponentiations, and 34,296 coefficient-product terms are instrumented integer/finite-field operation counts for the E-fiber kernel only. They exclude source polynomial factorization, source-j evaluation, Sage validation, fixture loading, and launch. No isolated wall-time or full IC pipeline comparison was run. The local gate can now classify a newly found exceptional prime without iterating over its `p` possible E x-coordinates; locating large prime divisors of the exact norm numerators remains the next arithmetic search.
