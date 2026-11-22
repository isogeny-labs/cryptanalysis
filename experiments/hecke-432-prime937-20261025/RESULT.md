# All rational level-432 source points are cusps at p=937

An exhaustive cyclic-kernel census finds **zero noncuspidal** points of
\(X_0(432)(\mathbf F_{937})\). Independently, the weight-two Hecke trace
is \(902\), so \(\#X_0(432)(\mathbf F_{937})=937+1-902=36\).
The cusp denominator criterion gives exactly **36 rational cusps**.
Under the [certified normalized map](../hecke-432-map-identity-20261025/RESULT.md),
every cusp maps to the identity of \(B=432a1:y^2=x^3-16\). Thus the
entire rational image is the identity. Direct enumeration gives
\(\#B(\mathbf F_{937})=999\), leaving **998** B points outside the
rational image.

The [frozen protocol](protocol.json) selected p=937 to test the case
where the dual degree-three isogeny has three rational kernel points.
That arithmetic holds: \(\#B(\mathbf F_{937})=999\) and the two
finite points with \(x=0\), together with the identity, form its
rational kernel. The zero-source result makes this prime a source
availability control. `evaluate_sage.py` records zero projected rows;
its three-preimage branch is reserved for a nonempty source prime.

## Census and independent checks

`census_sage.py` scans all 937 \(j\)-values. It tests one representative
per generic quadratic-twist pair, three sextic-twist representatives
at \(j=0\), and two quartic-twist representatives at \(j=1728\).
For every model it enumerates nonbacktracking cyclic 16- and
27-isogeny chains. None supplies a pair. The Hecke computation gives
36 total rational modular-curve points, and the independent cusp
formula gives 36, so the chain count meets its preregistered gate.

`audit.py` checks the frozen intermediate-map hash, the zero source
and projection rows, the Hecke-minus-cusps equality, both isogenous
curve orders, and the three-point rational dual kernel. Its finite
field square count gives 999 points on both B and
\(E:y^2=x^3+432\).

The [next-prime screen](screen_result.json) applies a fixed rule:
choose the smallest prime greater than 937 with
\(p\equiv1\pmod{12}\) and a positive noncuspidal count from the
Hecke-minus-cusps formula. It selects **p=997**. That prime has
\(\#X_0(432)(\mathbf F_{997})=1836\), 36 rational cusps, and
**1,800** noncuspidal points; \(\#B(\mathbf F_{997})=1008\), so it
retains a rational degree-three kernel. The screen records the
selection rule and every screened prime.

## Proof map and replay

| Result | Evidence and formalization |
| --- | --- |
| No noncuspidal rational source points | Full all-\(j\) chain scan in `census.json`; independent Hecke count 36 minus cusp count 36. |
| Full B image is the identity | Prior cusp-image theorem; `Prime937CuspImage.image_is_identity` proves the finite-source implication from all source points mapping to the identity. |
| Exactly 998 missing B points | Direct target order 999 and `Prime937CuspImage.exactly_998_missing`. |
| p=997 selected for the three-preimage test | `screen_next_prime_sage.py` and `screen_result.json`; Hecke and target-order calculations. |

The pinned Lean module builds and its `#print axioms` output lists only
standard foundations. Its hypotheses expose the remaining modular-map
and source-curve formalization bridge; the exact computations and
written modular arguments remain in the linked experiments.

Replay from the repository root with the checked launcher:

```sh
./sage --runtime-info
./sage -python experiments/hecke-432-prime937-20261025/census_sage.py
./sage -python experiments/hecke-432-prime937-20261025/evaluate_sage.py
./sage -python experiments/hecke-432-prime937-20261025/screen_next_prime_sage.py
python3 experiments/hecke-432-prime937-20261025/audit.py
```

The runtime receipt, protocol, full source and projection JSON,
independent audit, Lean build log, and checksum seal bind the result.
