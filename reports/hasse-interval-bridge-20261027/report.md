# Centered Hasse interval bridge: scoped proof review

2026-10-27 UTC · Conductor T-503 · producer commit `f4489073826e85854ebb1a142db9e94c957d9794` · review-plan commit `110b6b3`.

## Observation

`CurveAudit.unique_multiple_from_center_bounds` is a Nat theorem: two multiples of `r` within the same symmetric center-radius interval coincide if `2*radius < r`. Source SHA-256 is `f72e23b6d89fa7259b2502348b5af850bc18b8cf5f429b143a7292427358c400`; pin SHA-256 is `d5edba4e4b8faad9c1baeadb265716d20d03be4d1a2647dc5e35b0c0325bea7b` (Lean 4.34.1). It reduces to the previously reviewed short-interval lemma.

The isolated pinned Lean build and transitive axiom audit passed. The audit names both `CurveAudit.unique_multiple_from_center_bounds` and `CurveAudit.unique_multiple_in_short_interval`, each with axioms `[propext, Quot.sound]`; it reports zero failures and zero `native_decide` trusted exceptions. A compiled `False := by sorry` was rejected by the axiom audit, and an unknown module was rejected. Source, pin, auditor, and control input hashes were unchanged across their machine steps. Raw output and exact commands are in `attempt-1-machine-receipt.json` and `control-correction-receipt.json`.

The first boundary control failed to parse because its generated fixture had literal `\u` escape text in place of Lean operators. This was a control transcription error, not a theorem failure. Its logs and fixture remain under `attempt-1-*`; the corrected control was rerun separately and its logs and receipt retained. The initial receipt correctly reports `expected_exits_met=false`.

## Comparison and independent review

Reviewer A independently derived the statement from the blind brief, checked satisfiability and the zero cases, and supplied a boundary counterexample. Reviewer B checked source-to-proof-map fidelity and the curve-order boundary. Their reports and self-reported source-access attestations are included. B disclosed reading generic process skills and one unrelated memory search hit beyond the plan's literal four subject files. B read no A material and did not gain subject evidence from those extra reads. This is a disclosed protocol deviation; it limits a strict file-isolation claim, although the semantic work remained separate. Neither reviewer ran Lean; the coordinator owns machine validation.

## Verdict table

| Claim | Machine | Fidelity | Overall |
| --- | --- | --- | --- |
| Conditional centered Nat interval uniqueness | Exact-source pinned build and axiom audit passed; controls recorded | Two distinct reviews support; B access deviation disclosed | Validated scoped, conditional on the stated Nat premises |
| Complete P-192/P-224 curve-order proof in Lean | Missing bridges | Proof map explicitly marks partial | Not verified |

## Inference and limits

The new lemma correctly bridges symmetric center bounds to the prior uniqueness theorem. It does not establish that an actual elliptic-curve cardinality is a multiple of `r`, obeys Hasse's bound, or equals the proposed P-192/P-224 order. Prime-field, exact point-order, Lagrange, Hasse, squared-bound-to-radius, and concrete-input bridges remain open. The installed pinned Lean kernel is the machine trust boundary; an independent `lean4checker --fresh` pass was unavailable. The reviewer access attestations were not monitored at OS level.

No experiment was launched and no performance observation was added. Existing quantitative performance graphs have no new values to update. The diagram `proof-boundary.svg` shows the logical claim boundary; its source is the SVG itself. Related predecessor review: PR #1197 and `reports/hasse-unique-proof-review-20261027`.
