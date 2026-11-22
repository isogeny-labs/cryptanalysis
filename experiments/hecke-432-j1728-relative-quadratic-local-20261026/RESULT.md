# Local index exponents for the j=1728 quadratic relative factors

The two irreducible quadratic factors of the quartic over `L=K(√2)` are **unramified at every place above 7, 11, 23, and 31**. Their positive polynomial-discriminant valuations are all exactly two. Thus each affected place contributes one to the local index of the monic quadratic order in the maximal local order; places with valuation zero contribute zero.

| Rational prime | Places above p in L | Positive local index exponents for each conjugate quadratic factor | Odd discriminant valuations |
| ---: | ---: | --- | ---: |
| 7 | 18 | three degree-2 places, exponent 1 each | 0 |
| 11 | 18 | three degree-2 places, exponent 1 each | 0 |
| 23 | 20 | two degree-1 and two degree-2 places, exponent 1 each | 0 |
| 31 | 18 | none | 0 |

The factor coefficients are integral at every selected place and both factors are monic and irreducible. For `g(T)=T²+bT+c`, the exact coefficient check gives `Δ=b²−4c` and the identity `(2θ+b)²=Δ` for a root `θ`. At an odd-residue-characteristic place, write `Δ=π^{2k}u` with `u` a unit. Then `η=(2θ+b)/π^k` is integral and satisfies `η²=u`. The reduction of `T²−u` is squarefree because `2` and `u` are units. Its local algebra is therefore étale: it may split or remain inert, but is unramified. The change of generator gives local order-index exponent `k=v(Δ)/2`. This argument applies to every saved place; the run finds only `k=0` or `1`.

[`protocol.json`](protocol.json) freezes four input hashes and a 300-second cap. [`run_sage.py`](run_sage.py) reconstructs the exact factors over `L`, checks monicity, irreducibility and the discriminant coefficient identity, then computes all prime-ideal valuations and norm weights. The checked-Sage execution completed in about 22 seconds; [`sage-runtime-info.txt`](sage-runtime-info.txt) and [`attempt.json`](attempt.json) record the selected build and run. The full ideal generators, coefficient valuations, discriminant valuations, derived local-index exponents and norm-weight sums are in [`result.json`](result.json). [`audit.py`](audit.py) independently replays the parity, coefficient-integrality, index-exponent and norm-weight arithmetic from saved integers; its output is [`audit.json`](audit.json). The ideal valuations themselves are supplied by checked Sage.

## Proof map

[`formal/QuadraticLocal.lean`](formal/QuadraticLocal.lean) proves the universal completed-square identity over an arbitrary commutative ring and checks all four exact finite valuation tables, including parity, derived index exponents and weighted norm sums. [`formal/lean-check.txt`](formal/lean-check.txt) records successful builds and `#print axioms`; the table proofs use no axioms, while the universal polynomial identity uses standard `propext`. Formalization of the local DVR, its prime ideals, and the étale criterion remains **partial**. The exact open bridge is to define these concrete places in Lean and prove that each Sage-computed discriminant valuation equals its saved table entry, then formalize the odd-residue-characteristic quadratic unramified criterion.

The next calculation should classify the residue square class of each normalized unit `u` to distinguish split from inert places, and apply a comparable local-maximal-order test to the degree-four relative factors of the octic. The disjoint prime-ideal support at 23 from [the previous experiment](../hecke-432-j1728-relative-ideal-overlap-20261026/RESULT.md) remains a control when comparing the two discriminant components.
