# Proof map

| Result | Lean declaration or finite evidence | Status and exact hypotheses |
| --- | --- | --- |
| Odd Boolean coordinate sum plus all pairwise squarefree zero equations select one coordinate | `PartialIdeal.quadratic_onehot` in `OneHot.lean` | Checked with Lean 4.34.1; `parity` is fold-XOR and `quadratic` recursively forbids a second true coordinate; `#print axioms` reports only `propext`. |
| An independent family of distinct reciprocals has exactly the displayed one-hot equations in its own span coordinates | `PartialIdeal.quadratic_onehot` plus elementary uniqueness of basis coordinates | Structural theorem checked at Boolean coefficient level. The field-linear basis-coordinate map is not formalized in Lean. |
| N41 selected family sizes, ranks, S3 matches and group hits | Frozen `result.json`; selected independent `audit_result.json` | Finite native computation, six selected cases independently replayed in checked Sage. Field and curve operations and all 196 records are not imported into Lean. |
| At most 40 independent reciprocal values in these N41 families | Trace-zero checks in `joint_core.hpp`, rank bounds in `result.json`; previous trace theorem in `../n41_bilinear_rank_screen_20261013/BilinearGate.lean` | The 40-dimensional trace-zero-space bridge is used mathematically; it is not proved as an exact field-specific Lean theorem in this module. |

To formalize the complete finite result, define the pinned `GF(2^41)` representation and curve law in Lean, import the frozen state table and region construction, prove the reciprocal trace-zero property, and kernel-check the computed ranks and group hits. The written result keeps the computational evidence separate from the checked Boolean theorem.
