# Proof map: binary Frobenius target selector

The circuit changes only the representation of a choice among four raw
preimages and 131 Frobenius conjugates. The nine-pair source, balanced
addition tree, inverse-trace endpoint gates, and distinct-column shield
remain those of the immediately preceding experiment.

| Result | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Binary-controlled composition of iterated Frobenius steps selects the iterate at the sum of selected weights | `BinaryFrobenius.selectOrbit_correct` | Arbitrary type and endomap `step`; list of natural weights and Boolean choices | Checked in Lean; the theorem is unconditional |
| The selected fiber followed by the binary-controlled orbit equals the corresponding iterate of that fiber | `BinaryFrobenius.binary_target_correct` | Four input values, two Boolean fiber bits, arbitrary endomap and weights | Checked in Lean; `#print axioms` reports only standard `propext` |
| The XCNF mux implements this selector on the concrete N41 public target and rejects out-of-range rotations | Concrete Boolean-circuit bridge | GF(2^41) defining polynomial, all four raw preimages, 41 Frobenius rotations, native-XOR circuit semantics | All 164 valid choices and 92 invalid codes checked against Sage in `n41_control_result.json` |
| The XCNF mux implements the N131 target orbit | Concrete Boolean-circuit bridge | GF(2^131) defining polynomial and the frozen 524-choice target table | Constructed assignment checked in `control_result.json`; all-choice differential audit is `selector_524_result.json` when complete |
| A relation on a selected conjugate pulls back to the public subgroup point | `NinePairOrbit.relation_pullback` in the prior orbit experiment | Additive inverse Frobenius, source closure, and `[4]U=Q` | Prior conditional Lean theorem; the concrete curve bridge remains open |

The pinned `lean-toolchain` and `lean_runtime.txt` identify Lean 4.34.1 and
its bundled `Std`. Run `lean BinaryFrobenius.lean` in this directory; the
recorded `lean_check.txt` includes the `#print axioms` output.
`lean4checker --fresh` is unavailable on this host. Full formalization of
the concrete selector would need formal definitions for both binary fields,
the Frobenius linear maps, the CNF/native-XOR gate semantics, and the
public-point orbit tables. The abstract composition theorem and exhaustive
executable controls do not close that bridge, so it remains partial.
