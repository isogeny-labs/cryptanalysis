# Proof map

| Mathematical result | Formal or computational evidence | Status |
| --- | --- | --- |
| `Tr(z²+z)=0`, so all cross columns lie in the trace-zero hyperplane | `BilinearGate.artin_schreier_trace_zero` and `bilinear_column_trace_zero` in `../n41_bilinear_rank_screen_20261013/BilinearGate.lean`; prior pinned Lean 4.34.1 build and `#print axioms` record | Lean checked for the stated generic trace laws |
| If `dim C+dim D>n`, the cross-column span is the trace-zero hyperplane | Written proof in `RESULT.md` using the nondegenerate finite-field trace pairing, Frobenius fixed field, and annihilator dimension | Faithful Lean formalization remains open: the local Std-only theorem module does not define finite-field trace pairing, subspace annihilator dimensions, or their bridge to the concrete coordinate spaces |
| Complete N41 region-rank histogram at every prefix level | `result.json` and independently reconstructed `audit_result.json`; frozen sources, caps, and replay receipts checked by `verify.py` | Complete finite computation with independent Sage replay; no Lean certificate import |
| Exceptional four-family self-pair has cross rank 40 | `exception_result.json` and independent Sage `exception_audit_result.json` | Complete finite computation with independent Sage replay; no Lean certificate import |
| Every ordered region pair with four or more product families survives this linear span screen for the declared public target | Dimension theorem plus complete rank histograms, one exceptional cross-rank computation, and target trace-zero check | Written mathematical derivation and checked finite inputs; Lean bridge remains partial |

The formalization attempt used the pinned Lean 4.34.1 toolchain. The exact
`lean LeanProbe.lean` import probe is retained in `lean_attempt.log`; the
local environment reported `unknown module prefix 'Mathlib'`. No weaker
Boolean or abstract-rank declaration is presented as a Lean proof of the
general dimension theorem. A faithful Lean completion needs finite-field
trace, the Frobenius fixed-field lemma, perfect trace pairing, rank-nullity
for annihilators, and checked imports of the finite rank certificates.
