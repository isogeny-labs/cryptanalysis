# Proof map for direct quartic evaluation

| Result | Lean declaration | Exact hypotheses and verification |
| --- | --- | --- |
| Four Horner multiply-add steps equal evaluation of an arbitrary quartic | [`DirectRoot.horner4_eq_poly4`](DirectRoot.lean) | Arbitrary commutative ring, five arbitrary coefficients and any evaluation element. Checked. |
| Two direct Horner zero tests have exactly the common-root witnesses | [`DirectRoot.two_horner_zeros_iff_common_root`](DirectRoot.lean) | Arbitrary commutative ring and two arbitrary quartics; the same existential witness appears on both sides. Checked. |
| The N41 circuit coefficients are the exact source-pair quartics | The frozen [builder](build.py) shares the prior quartic construction; its source hashes, 33 complete assignments and the independent source-panel audit are checked by [the verifier](verify.py) | Finite instance checked. A Lean model of the field, curve, aligned source table and Boolean circuit remains open. |
| A common root gives the intended five-pair curve relation under source-valid states | The [prior split-root proof map](../n41_w9_two_quartic_resultant_20261017/PROOF_MAP.md) and independent Sage group replay of any SAT model | The abstract polynomial implication is checked; the concrete curve/source bridge is finite-audited and open as a Lean theorem. |

Build from this directory: `lean DirectRoot.lean > lean_check.log 2>&1`.
The pinned `lean-toolchain` selects Lean 4.34.1. The [build output](lean_check.log)
reports only `propext`, `Classical.choice`, and `Quot.sound` for both
declarations. The module uses no `sorry`, `admit`, `sorryAx`, custom research
axiom or native evaluation. A fresh `lean4checker` run is unavailable here.
