# Known-label algebra: recovered technical evidence review

Recorded 2026-10-29. Archive task TASK-20261028-871ca0; Conductor T-765.

## Scope and outcome

Four exact commutative-ring identities have passing native Lean compilation and transitive axiom audits on producer `0b353c9bf78e9340c3c100b71175127bb7d91d44`. The independent mathematical and source-fidelity reviews support those identities. The revised verifier passed its independent static and admission-behavior review. The broader cryptanalysis claims and the complete formal-review gate remain open: no independent comparison against printed elaborated declaration types has been archived. This packet makes no experiment, speed, security, or full historical-validation claim.

The original producer called Algebra.lean proposed and unbuilt. Its historical CHECKS.json is preserved. Native evidence here is a later result and does not retrospectively change that record. The first verifier review found two defects; its report remains unchanged beside the revised review.

## Bound inputs and chronology

- Source: `docs/known-label-next-leads-20261028/Algebra.lean`, SHA-256 `d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d`.
- Workspace: `experiments/hecke-432-formal-ci-20261025`; Lean `v4.35.0-rc4`; Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. Exact three project-file hashes are in inputs-v2.json.
- Original plan and inputs were pushed at commit `dcebcd1842d112ebc3d985f02245cf0a8b7a8391` before dispatch. Revised J3 plan was pushed at `35ed5772e98fb3c8754b7fb6367d7ae1ebd83188` before the affected-joint re-review.
- Native run 40741310214, attempt 1, job 123003327508 checked producer `0b353c9bf78e9340c3c100b71175127bb7d91d44` through GitHub's synthetic merge `6d2e09d15` into base `47865467f9cc28c316a12ddab017017047815f19`. The job completed successfully at 2026-10-28 18:16:29 UTC.
- Main advanced to `80231e58a4dfa32951309fe365c39dfa569d79dc` during migration and contains a separate admission implementation. This packet reviews its bound producer, not that new implementation. PR1284 must reconcile the source conflict and obtain fresh exact-head checks before merging.

## Observations: native machine evidence

The full decoded job log, job/run metadata, line references and SHA-256 are archived under native-ci/. The gate compiled the original source into a temporary module and audited all four non-internal theorem declarations. The log reports four audited theorems, zero failing and zero trusted exceptions. Actual foundations were propext for triangle_identity, and propext plus Quot.sound for the other three. No custom axiom or sorryAx was reported.

The same job's native controls passed: Positive was accepted; Assumed was rejected for its unproved axiom; Empty was rejected for zero theorems; IllTyped failed elaboration. Python admission tests and the independent mock diagnostic are separate software evidence, not native proof evidence. The corpus log's 70 added modules and reused frozen archive do not establish semantic coverage of every historical experiment.

## Per-claim status

All identities quantify over an arbitrary commutative ring K and a,b,c in K. Let D=(a-c)*(b-c).

| Exact declaration | Statement | Machine | Independent fidelity | Review outcome |
| --- | --- | --- | --- | --- |
| KnownLabelLeads.triangle_identity | 2*a=(a+b)-(b+c)+(c+a) | passed | source statement faithful; elaborated type not reviewed | inconclusive for complete formal-review gate |
| KnownLabelLeads.signed_second_moment | (a+b-c)^2-(a^2+b^2-c^2)=2*D | passed | source statement faithful; elaborated type not reviewed | inconclusive for complete formal-review gate |
| KnownLabelLeads.signed_third_moment | -(a+b-c)^3+3*(a+b-c)*(a^2+b^2-c^2)-2*(a^3+b^3-c^3)=6*c*D | passed | source statement faithful; elaborated type not reviewed | inconclusive for complete formal-review gate |
| KnownLabelLeads.positive_pair_product | 2*a*b=(a+b-c)^2-(a^2+b^2-c^2)+2*c*(a+b-c) | passed | source statement faithful; elaborated type not reviewed | inconclusive for complete formal-review gate |

The plain algebraic statements are supported independently and machine checked. The stricter validated_scoped review label is withheld until the remaining declaration-type evidence is independently checked. None of the rows asserts a recovery algorithm or a probability bound.

## Comparison: independent reviews and controls

J1 (TASK-20261028-32bc7d) independently derived the four expressions from a mathematical-only brief, without the producer's answers, proof text, repository, or sibling reports. Its verdict holds over arbitrary commutative rings, including characteristics 2 and 3, the zero ring and rings with zero divisors. It exhibited invalid strengthened conclusions: cancellation by 2 fails in characteristic 2; division by D needs D to be a unit and fails for coincident elements or nonzero zero divisors.

J2 (TASK-20261028-a07ed4) compared exact source declarations with the stated algebraic scope and listed missing research bridges. Its source-level verdict holds. It explicitly did not inspect elaborated types, so its attestation is not presented as that missing review.

Original J3 (TASK-20261028-298dc6) found two verifier defects on producer ffeacb44b6a151aebc84619f30a70591eb44e0f6: project files changed during native commands could still pass, and manifest-only changes missed both automatic workflow filters. Revised J3 (TASK-20261028-68d1a5) used the unchanged independent diagnostic against producer 0b353c9. All six persistent mutation cases (three files, during compilation or audit) now reject. Both workflow event filters include the manifest. Nineteen existing tests passed; the independent diagnostic recorded 21 cases, 19 refusals and two acceptances.

The two acceptances are the valid mock baseline and contradictory fabricated auditor output paired with a zero exit status and success summary. The latter documents trust in the declared auditor's output protocol; it is not evidence that the unmodified native auditor accepts a bad axiom. Pre/post hashes detect persistent mutation, not a transient edit restored between checks. Executables and dependency binaries remain trusted. The revised J3 verdict holds only within those boundaries, and supplies no native proof verdict itself.

Round-one and round-two independence checks passed using the pinned checker revision and the exact three attestations for each round. Original J1/J2 rich attestations were preserved; reviewers supplied additive path-string formats after the checker rejected the originals. The first failure and the original J3 breaks verdict remain archived. The original J3 handoff's omitted per-task source entry and its dispatch clarification remain recorded as a procedure deviation, not erased.

## Inference and outstanding bridges

The algebraic identities need no characteristic exclusions. Algorithms that divide their coefficients need additional hypotheses. A bridge to actual elliptic-curve point relations requires a specified scalar-to-group homomorphism, verified points/subgroup and field, coefficient consistency, graph propagation and anchor conditions, and nonzero extraction coefficients. None follows merely from ring normalization.

Finite-field signature recovery needs the intended prime field and characteristic restrictions, the index embedding and bounds, distinct indices and nonzero denominators, root/ordering uniqueness, rank conditions and a connection between point relations and polynomial signatures. Probability claims require the actual sampling model, event probabilities and dependencies, second-moment and bad-event bounds, and justification for transfer to the structured graph. The proposed asymptotic and cost conclusions remain unproved here.

Next proof-review step: retain exact elaborated types from the pinned native module and give those artifacts to an independent fidelity reviewer under a prospective supplement. Next delivery step: reconcile PR1284 with advanced main without dropping either implementation's controls, then obtain current-head CI. Full historical experiment-to-proof mapping, execution replay, graph refresh and dashboard publication remain the original task's requirements.

## Visuals and migration recovery

proof-boundary.svg and report.pdf are new derived views of this packet. There are no comparative measurements to plot, so the diagram shows the evidence boundary. The original study's diagram.svg/REPORT.pdf describe its proposal and are not replaced by a claim of full proof. This packet is linked to the exact source and review artifacts; no canonical performance number changes.

The prior host's uncommitted render files did not survive at their /var/tmp path. Durable reviewer artifacts, native Git commits and the old render-preview images survived. The current report and visual were reconstructed from those immutable inputs and the newly retrieved native log; the old preview is not presented as current. Reviewer files are copied byte-for-byte and checked against their SHA manifest. No reviewer or experiment was restarted.

## Evidence links

- [Native CI run](https://github.com/isogeny-labs/cryptanalysis/actions/runs/40741310214/job/123003327508)
- [Producer PR1284](https://github.com/isogeny-labs/cryptanalysis/pull/1284)
- [Review PR1285](https://github.com/isogeny-labs/cryptanalysis/pull/1285)
- review-plan.json, review-plan-v2.json, inputs.json, inputs-v2.json, dispatch-receipt.json
- reviewers/TASK-20261028-32bc7d/report.md; reviewers/TASK-20261028-a07ed4/report.md
- reviewers/TASK-20261028-298dc6/report.md; reviewers/TASK-20261028-68d1a5/report.md
- independence-round1.json, independence-round2.json, native-ci/receipt.json, render-receipt.json
