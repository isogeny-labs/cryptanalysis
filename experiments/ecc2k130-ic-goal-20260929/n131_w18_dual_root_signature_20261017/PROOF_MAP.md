# Proof map

The reusable structural result is `DualRootSignature.paired_roots_agree` in
[`DualRootSignature.lean`](DualRootSignature.lean). It is quantified over an
arbitrary type `F` with a specified characteristic-two addition, a Boolean
linear functional, a predicate `U`, and two roots whose sum lies in `U`.
The functional must vanish on `U`. It proves equal functional values at the
two roots. `zero_functional_on_pair` adds the hypothesis that the first root
has value zero and proves the same for the second.

Both declarations build with pinned Lean 4.34.1 using
`lean DualRootSignature.lean`. The saved [`lean.stdout`](lean.stdout) reports
only the standard Lean axiom `propext` for each; [`lean.stderr`](lean.stderr)
is empty. `lean4checker --fresh` was unavailable in this environment.

The bridge to this instance is a finite, independently replayed computation:
[`audit.py`](audit.py) checks the 33,191 saved root pairs, the rank-17 span of
their XOR differences, 114 independent annihilating masks, and each mask's
equal value on every saved pair. This is a data-dependent computation, not a
Lean proof of the entire enumerated table or of the source's elliptic-curve
formulas. The source's earlier independent Sage audit checked all 66,382
roots and 265,528 signed point additions; the table and that audit are
identified in [`RESULT.md`](RESULT.md).

The exact restricted-code ANF intersection ranks and the 130-dimensional
root-output span are finite computations independently replayed by
[`audit.py`](audit.py) through degree five. The separately frozen degree-six
extension is computed by [`degree6.py`](degree6.py) and independently replayed
with low-pivot elimination by [`degree6_low.py`](degree6_low.py). A Lean theorem for those
particular 33,191 by 21,778 matrices is not yet available; the full
instance-level formalization remains partial at the matrix-rank bridge.
