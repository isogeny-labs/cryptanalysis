# Centered interval Lean bridge: pre-dispatch review plan

2026-10-27 05:09 UTC · Conductor T-503. The producer source is immutable
commit `f4489073826e85854ebb1a142db9e94c957d9794` in cryptanalysis.
The reviewed declaration is `CurveAudit.unique_multiple_from_center_bounds`
in `bindings/rust/curve-audit/formal/HasseUnique.lean`, SHA-256
`f72e23b6d89fa7259b2502348b5af850bc18b8cf5f429b143a7292427358c400`.
The pin is `leanprover/lean4:v4.34.1`, pin SHA-256
`d5edba4e4b8faad9c1baeadb265716d20d03be4d1a2647dc5e35b0c0325bea7b`.
The proof map SHA-256 is
`fb2a563b338c30a028fc942b467b319237109b5288bc0b1c7dfc1efd4bd1d71d`.
The original uniqueness theorem and its scoped review are at producer base
`dc73f979...` and PR #1197; this change adds a conditional bridge from
symmetric center bounds and does not alter the original declaration.

## Prior and reviewer joints

Prior, recorded before reviewer reports: local precheck on the exact new
source succeeded under Lean 4.34.1; the mathematical implication appears
valid and nonvacuous. The full P-192/P-224 curve-order bridge is still
unfinished because the theorem assumes the actual cardinality is a multiple
of `r` and both numbers satisfy the center bounds. A reviewer may disagree.

| Joint | Owner | Attack or discriminator |
| --- | --- | --- |
| General Nat statement, quantifiers, satisfiability, sharp diameter bound | Blind reviewer A | Re-derive from `blind-brief.md` alone. Try `r=0`, radius zero, and the boundary `radius+radius=r`; find a concrete false weakened case if possible. |
| Lean source-to-proof-map fidelity and curve-order claim boundary | Source reviewer B | Compare exact declaration with the proof map and README. Look for assumed conclusion, wrong inequality orientation, missing multiplicity premise, or an arithmetic lemma misreported as Hasse/Lagrange. |
| Exact source build, transitive axioms, positive/negative controls | Coordinator | Rebuild isolated Git blobs at pinned Lean, audit named theorems, test a nonvacuous case and a boundary counterexample, and retain raw logs and hashes. |

Reviewer A may read only `blind-brief.md` and, if needed, public Lean/Nat
documentation; A must not read repository source, proof map, this plan,
machine logs, or B's report. Reviewer B may read the bound source, proof map,
producer README, and this plan, but not A's material. Each reviewer reports
all actual sources read, sibling access, owned joints, protocol deviations,
and `holds | breaks | inconclusive` findings. Both deliver to separate
scratch files; the coordinator composes only after both return.

Positive control: `r=7`, `radius=1`, `center=n=m=14`, `k=l=2`. Known-false
nearby control for a weakened diameter `radius+radius≤r`: `r=6`,
`radius=center=3`, `n=0`, `m=6`, `k=0`, `l=1`; the remaining premises hold
but equality fails. The controls must be checked by Lean and their scope
reported. A false-control proof with `sorry` must fail the transitive axiom
audit. A wrong module must not pass an empty audit.

The machine, fidelity and overall verdicts remain separate. `validated_scoped`
can apply only to the stated Nat implication after exact-source native
verification, controls, and independent semantic review. It cannot apply to
the full elliptic curve order claim without formal prime-field, point group,
Lagrange, Hasse, squared-bound, and concrete-input bridges. No official
research status or benchmark changes here.
