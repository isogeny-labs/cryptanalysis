# Independent known-label Lean proof review

**Task:** T-1299. **Producer pin:** `52baa40a94751916c0d8b83ec8691125bccdac3c`.
**Machine run:** [cryptanalysis corpus 41344355706](https://github.com/isogeny-labs/cryptanalysis/actions/runs/41344355706), successful at `6ad8b68d8d79bb31e8f915915f844796344d8b57` with the same reviewed source bytes. This is a technical proof review; it does not change a hypothesis or official evidence decision.

## Observation

The native gate reported 4/4 `KnownLabelLeads` and 7/7 `KnownLabelPairIndex` named declarations, their elaborated types, an exhaustive audit and allowed transitive axioms (`propext`, `Classical.choice`, `Quot.sound`). It reported zero failing or trusted exceptions. The source hashes are `d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d` for `Algebra.lean` and `68dd10106b5499ad8b3fba35b95980a5ed1e6c46c0433047e0d5034e90c135c8` for `PairIndex.lean`. The separate source review recomputed both. This hosted source-bound run is fresh native machine evidence relative to the archived receipt, but this review did not run a second local Lean build or independent kernel binary.

The [blind review](blind-math-review.md) derived the triangle formula `2R₀ = T₀₁ − T₁₂ + T₂₀` from three verified edge equations and the affine closed-path equation `(1−A)z₀=C` from the recurrence. Its `F₅` two-step example has `A=1,C=0`, so every start closes; changing one offset gives `A=1,C=1`, so none closes. The [source-fidelity review](source-fidelity-review.md) separately checked the pinned Lean hypotheses and the producer's executable and cost claims. Both reviewers attest that they did not read the other's report before filing.

## Per-claim verdict

| Claim/declaration | Machine | Fidelity to stated algebra | Review outcome |
| --- | --- | --- | --- |
| `KnownLabelLeads.triangle_identity`, `signed_second_moment`, `signed_third_moment`, `positive_pair_product` | passed, four names | faithful_scoped: commutative-ring identities | validated_scoped as identities; no division, edge validation, or decoder theorem |
| `KnownLabelPairIndex.affine_composition`, `cycle_recovery` | passed, two names | faithful_scoped: module equality and conditional recovery with `a≠1` | validated_scoped at the module hypotheses |
| `KnownLabelPairIndex.affine_path`, `cycle_constraint`, `label_recovery`, `signed_square`, `semaev_pair_identity` | passed, five names | partial for a verified graph or executable interpretation | needs_revision if cited as a concrete point/algorithm certificate; the displayed algebra remains valid |

The per-declaration types and exceptional cases are transcribed in [source-fidelity-review.md](source-fidelity-review.md). In particular, `cycle_constraint` assumes the fixed-point equation; `label_recovery` assumes both a nonzero coefficient and the target equality; `signed_square` assumes four recurrences; `semaev_pair_identity` is a cleared polynomial identity under two curve equations and does not license division by `(x−y)²` or certify a pair-index output. The ring triangle identity remains true in characteristic two but does not invert doubling there. An empty path and trivial module satisfy abstract equalities without producing a relation.

## Interpretation and next construction

The triangle and affine-recovery algebra is independently supported at its quantified hypotheses. The concrete bridge needs a checked elliptic subgroup and order, a `ZMod r` scalar action on its points, verified oriented edge equations and path closure, a nonzero recovery coefficient, and final scalar/point replay. The Python fixture checks one supplied curve and deterministic controls; its API leaves untrusted input validation and final-candidate certification to a driver. The written `Õ(n²+N+C)` field-operation bound is a model, with no Lean complexity theorem or matched measured end-to-end cost. The next useful proof is a constructor that maps a checked signed edge into the point-group affine update, followed by a closed-walk theorem with explicit coefficient and replay premises.

## Controls, independence and limits

The source reviewer traced gate refusals for missing names, custom axioms, empty/failing audits and ill-typed fixtures, and ran dependency-free empty/even/unbalanced/characteristic-two behavior controls. The full local Python suite stopped at missing `sympy`; its archived ten-test receipt is producer evidence, not a new local test. The blind reviewer supplied the `F₅` balanced-cycle counterexample. No new benchmark or experiment was run.

The [precommitted plan](review_plan.md) assigned J1/J3/J4 to source fidelity and J2 to blind mathematics before either report. Reviewer access statements are in their reports. The repository's `check_review_independence.py` expects a YAML `review_plan` block; when run on this Markdown plan it exited 2 with `no review_plan block`. We retain that result as an instrumentation mismatch and rely on the published plan plus reviewer attestations, not a claimed automated independence pass. The reviewers' isolation was not mechanically enforced. The hosted Lean job is source-bound but no separate local build or independent kernel binary ran in this task.

## Visual record

The [editable diagram](proof-boundary.svg) and [PDF](report.pdf) show the proved algebra and the exact application obligations. Existing `docs/known-label-next-leads-20261028/diagram.svg` and `docs/known-label-pair-index-20261029/diagram.svg` were checked; this review changes no underlying experiment, lead coverage or measurement, so their earlier figures remain historical and unchanged. There are no quantitative proof-review data to plot.
