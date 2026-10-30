# Xedni proof elaboration correction

The published diagnostics identified the actual failing source: WitnessObstruction.lean at source832e01578, run41042594820/job124018778233. The bounded-witness control used decide before removing a free Fin variable. The unbounded-relation control left a cast successor nonzero goal and normalized the cast before natAbs could reduce.

The correction uses an explicit definitional goal change, the constructive core lemma Int.ofNat_ne_zero with Nat.succ_ne_zero, and direct natAbs reduction. All five theorem statements, the first three proof bodies, reduction/witness hypotheses and quantifiers are unchanged. The dependency record binds the corrected source hash while still marking its native project build pending. All nine original sealed20261028 files remain unchanged.

Three core-only compatibility controls actually compile with installed Lean4.34.1. The constant-bound control is axiom-free; the other two use only standard propext. This is a diagnostic for these arithmetic terms, not validation of the project at pinned Lean4.35.0-rc4/Mathlib021c46. Fresh native corpus compilation and all five foundation audits remain mandatory; the original review stays open until that succeeds. No tactic/proof escape, assumption, pin, timeout or admission rule was relaxed.

The complete current-source failed job log and local compatibility source/output are retained. Mathematical statements, source report/proof map, SVG and PDF are unchanged because only proof elaboration changes; no new mathematical or performance conclusion is asserted.
