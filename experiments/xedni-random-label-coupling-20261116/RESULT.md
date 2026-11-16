# Random-label coupling for collision-free xedni traces

**Theorem.** For two injective lists of group elements, there is a bijection
between all bijective label encodings that makes their complete observed
label tuples identical. The checked Lean proof shows that every event
depending only on those tuples has the same number of encodings for either
trace. Applied to affine public expressions aQ+bG, this gives equality of
pre-collision label-observation laws at any two target scalars for which
both evaluated traces are injective.

The proof extends the finite trace-point correspondence to a permutation
of the group, then precomposes an encoding with that permutation's inverse.
It is a coupling lemma for the random-bijection model in
[Shoup's generic-group analysis](https://www.shoup.net/papers/dlbounds1.pdf).
An adaptive group-oracle theorem additionally needs an induction showing
that the trace chosen from these observations remains paired at every
operation before collision.

## Exhaustive five-element encoding census

The frozen experiment uses the additive group Z/5Z, labels 0..4, all
**120** bijective encodings, and three affine expressions 0, w, and w+1.
Their evaluated traces are injective at w=1,2,3. At w=4, the first and
third elements coincide, giving a boundary control.

| Scalar | Group trace | Injective | Visible tuples | Encodings per tuple |
| ---: | --- | --- | ---: | ---: |
| 1 | (0,1,2) | yes | 60 | 2 |
| 2 | (0,2,3) | yes | 60 | 2 |
| 3 | (0,3,4) | yes | 60 | 2 |
| 4 | (0,4,0) | no | 20 | 6 |

The full tuple histograms at w=1,2,3 are identical. For w=2 and w=3,
the producer constructs an explicit group permutation and pairs all 120
encodings bijectively with those at w=1, checking every label tuple. The
w=4 histogram differs because injectivity fails. The independent audit
regenerates every histogram and checks the 60/60/60/20 tuple counts.

Run python3 run.py, python3 audit.py, and, from formal/, lake build
RandomLabelCoupling. The protocol, full histograms, couplings, audit, Lean
source and build receipt are sealed; python3 verify.py checks the packet.
The next proof step is a step-by-step generic-oracle coupling. A concrete
coordinate-selection experiment needs its own observed-input and cost law.
