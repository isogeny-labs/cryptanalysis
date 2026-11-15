# CRT curve choice for two-point xedni lifts

A deterministic CRT choice in the monic Weierstrass family constructs rational
curves meeting the frozen auxiliary orders at 7 and 11 for 1,344 of the
1,722 ordered point pairs on `E/F₄₇: y²=x³−x−2`. The accepted set contains
34 pairs with the reduced relation `P₁+2P₂=O`; two sign-related pairs also
satisfy `Q₁+2Q₂=O` on their reconstructed rational curves. The accepted
pairs occupy 672 distinct rational curves. This supplies an explicit
small-field rational-lift relation within the stated deterministic policy.

| Frozen arm | Input pairs | Accepted rational curves by pair | Reduced relation in accepted pairs | Rational relation in accepted pairs |
| --- | ---: | ---: | ---: | ---: |
| Full ordered distinct nonidentity `E(F₄₇)` law | 1,722 | — | 42 | — |
| One free coefficient `a₂` | 1,722 | 0 | 0 | 0 |
| Free `a₁,a₂,a₃` with CRT | 1,722 | 1,344 | 34 | 2 |

The base curve has prime group order 43. Its full reduced relation rate is
`42/1722 = 1/41`. The full-family accepted rate is `34/1344 = 17/672`, an
event enrichment of `697/672` relative to the full law. The rational
relation rate within accepted pairs is `2/1344 = 1/672`. The two rational
relation pairs are sign-related and share one underlying curve shape; these
finite-panel fractions are exact counts, not independent-trial estimates.

## Fixed public-point replay

The frozen public input `G=(2,2)`, `Q=(26,8)` has subgroup order 43.
With `s=(1,1)`, the replay enumerates every ordered pair
`(t₁,t₂)∈{0,...,42}²` and forms `Pᵢ=sᵢQ−tᵢG`. It runs the CRT coefficient
search afresh for each admissible pair; the saved census is used as an
independent row-by-row crosscheck. Of 1,849 queries, 1,722 have distinct
nonidentity sampled points, 1,344 pass the CRT gates, 34 have the reduced
relation, and two have the rational relation. Those two occur at
`t=(5,23)` and `t=(29,11)`. Each yields
`(t₁+2t₂)/3 = 17 (mod 43)`, and scalar multiplication reproduces `Q`.

The target scalar 17 was used only to construct and independently check the
fixture. The exhaustive target run is a correctness control with its own
frozen input law and complete compressed query statuses in
`target-rows.jsonl.gz`. It is not an online wall-time comparison; the
curve search and all 1,849 queries must be charged in any future cost study.

## Coefficient-search work on the fixed target

The saved target order first reaches a rational relation at `(t₁,t₂)=(5,23)`.
The probe-accounting extension joins every target query to the frozen parent
census and counts each coefficient candidate inspected by the deterministic
auxiliary search. An independent pure-Python audit replays the 7 and 11
finite-field searches for all 1,344 accepted pairs and matches every saved
attempt count and selected residue.

| Stop | Target queries | Admissible pairs | Accepted pairs | Reduced relations | Rational relations | Coefficient probes at 7 | Coefficient probes at 11 | Both primes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| First rational relation | 239 | 227 | 183 | 6 | 1 | 14,082 | 27,384 | 41,466 |
| Complete target scan | 1,849 | 1,722 | 1,344 | 34 | 2 | 106,612 | 201,702 | 308,314 |

These are exact candidate-probe counts for this fixed finite panel, not
elapsed time. They exclude reduced-point generation, CRT assembly, rational
group checks, and startup, so they are a lower bound on complete work. The
full-scan descriptive ratio is 154,157 coefficient probes per rational
relation; the two relations are sign-related and are not independent trials.
`cost-protocol.json`, `cost-result.json`, and `cost-audit.json` retain the
input hashes, ordered stopping rule, counts, and independent replay. Run
`python3 experiments/xedni-crt-curve-choice-20261115/cost_account.py --verify`
and `python3 experiments/xedni-crt-curve-choice-20261115/cost_audit.py` to
recheck them without Sage.

One checked witness uses the rational curve with Weierstrass coefficients
`[a₁,a₂,a₃,a₄,a₆]=[-987,-1034,0,7660,-3997]` and lifted points
`Q₁=(14,7)`, `Q₂=(17,10)`. The Sage run and an independent exact-rational
doubling audit check `Q₁+2Q₂=O`. Its reductions at 47 are the same affine
points and satisfy the same relation. Its reductions at 7 and 11 have 4 and
6 points respectively. The sign-related witness has `a₁=987` and negated
y-coordinates.

The pinned Lean module `formal/RationalWitness.lean` derives the rational
relation on the exact Weierstrass curve using Mathlib's affine elliptic-curve
group law, after checking the discriminant and both point equations. Its
companion `reduced_relation` theorem checks the relation on the exact
`ZMod 47` curve with the same reduced affine coordinates. The
`rational_model` and `reduced_model` theorems map one integer-coefficient
Weierstrass model to those two exact curves. All four `#print axioms`
results list only `propext`, `Classical.choice`, and `Quot.sound`.
The point-reduction and auxiliary order calculations remain in the exact
Sage and independent arithmetic audits.

The Lean module also constructs the fixed public points `G=(2,2)` and
`Q=(26,8)` on that finite-field curve and checks both point equations.
Its `public_scalar` theorem checks `17 • G = Q` with kernel evaluation of
the exact group law. The earlier plain-`decide` attempt stopped at repeated
point addition; its compiler output remains in
`formal/public-scalar-attempt.txt`. The Sage target replay and independent
arithmetic audit separately check the scalar identity and relation rows.
The `target_row_29_11` theorem additionally checks that the saved reduced
points satisfy `P₁=Q−29G` and `P₂=Q−11G` on that curve. Together with the
formal reduced relation and the `ZMod 43` recovery calculation, this gives
an exact checked chain for the `(29,11)` row.
The `target_row_5_23` and `mirror_reduced_relation` theorems check the
sign-related row. A second rational elliptic-curve theorem checks
`Q₁+2Q₂=O` for coefficients `[987,-1034,0,7660,-3997]` and points
`(14,-7)`, `(17,-10)`; its integral model also reduces to the exact
mod-47 curve. Thus both saved relation hits have checked curve, row, and
scalar-recovery components.

## Construction and boundary

For each pair, center the finite-field affine coordinates in `[-23,23]`.
At 7, search free coefficients `(a₁,a₂,a₃)` by increasing centered size for
the first nonsingular curve of order 4 through the two reduced lifted
points. At 11, seek order 6 first, then order 7. Combine each free
coefficient with the required zero residue at 47 by CRT modulo 3,619.
Solve the two rational point equations for `a₄,a₆`. The selected rational
curve must be nonsingular and reduce to the prescribed curve at all three
primes. The source checks the full incidence rank, curve orders, point
equations and group relations. The coefficient and arm choice is fixed in
`protocol-v2.json` before the full-family census.

The first frozen arm held `a₁=a₃=0` and varied only `a₂`. Its 1,722-row
census found 88 pairs with an order-4 candidate at 7, but none of those
pairs had an order-6 or order-7 candidate at 11. That arm and its zero-yield
rows remain in `protocol.json`, `run.py` and `rows.jsonl`. The widened family
accepts every pair whose lifted x-coordinates differ modulo 47, 7 and 11:
42 pairs fail the first check, 224 the second and 112 the third. It uses
the strict order-6 arm at 11 for every accepted pair; the frozen order-7
fallback has zero selected rows.

This implements a two-point coefficient CRT choice in one monic
Weierstrass family. The [original xedni algorithm](https://pages.cpsc.ucalgary.ca/~jacobs/PDF/xedni.pdf)
also allows auxiliary point CRT, more curve coefficients, and discriminant
optimization. The finite witness demonstrates that a universal
impossibility statement would be false; the relevant next mathematical
question is a bounded-probability theorem for the actual selection law and
height conditions as the field grows. The previously checked conditional reduction
and sampling theorems in the existing Lean modules apply only with their
stated bounded-witness and sampling hypotheses.

`PROOF_MAP.md` maps the scalar-recovery implication and both saved
`t`-pairs to three checked declarations in `formal/TargetRecovery.lean`.
The pinned build and `#print axioms` audit passed. The elliptic-curve
instantiation of the rational witness remains open in Lean. The current
shared checkout failed the older obstruction module's source-hash verifier,
so that module is not reported as freshly built here.

## Reproduction

The protocol and input law were frozen before each arm. The initial run of
the restricted arm stopped at JSON serialization before any pair row was
written. Its source, stderr and empty row file are retained as
`run-failed.py`, `run-failed.stderr` and `rows-failed.jsonl`; the corrected
run and full-family run both exited zero with empty stderr. Runtime receipts
record the accepted Sage source and native binary manifest.

```sh
./sage --runtime-info > experiments/xedni-crt-curve-choice-20261115/sage-runtime-info.json
./sage -python experiments/xedni-crt-curve-choice-20261115/run.py > experiments/xedni-crt-curve-choice-20261115/result.json 2> experiments/xedni-crt-curve-choice-20261115/run.stderr
./sage --runtime-info > experiments/xedni-crt-curve-choice-20261115/sage-runtime-info-v2.json
./sage -python experiments/xedni-crt-curve-choice-20261115/run_v2.py > experiments/xedni-crt-curve-choice-20261115/result-v2.json 2> experiments/xedni-crt-curve-choice-20261115/run-v2.stderr
./sage --runtime-info > experiments/xedni-crt-curve-choice-20261115/sage-runtime-info-target.json
./sage -python experiments/xedni-crt-curve-choice-20261115/target_replay.py > experiments/xedni-crt-curve-choice-20261115/result-target.json 2> experiments/xedni-crt-curve-choice-20261115/target.stderr
python3 experiments/xedni-crt-curve-choice-20261115/audit.py
(cd experiments/xedni-crt-curve-choice-20261115/formal && lake build TargetRecovery)
python3 experiments/xedni-crt-curve-choice-20261115/verify_formal.py
```

The large raw row streams are committed as `rows.jsonl.gz` and
`rows-v2.jsonl.gz` under the repository data-file limit; the result records
retain their uncompressed SHA-256 values. The independent `audit.py` checks
both source and runtime receipts, all
1,722 input pairs, every accepted curve equation and finite-field order,
the reduced group relation, the rational relation by an exact doubling
formula. It preserves all failed construction statuses and checks the
two rational witnesses. It also independently recomputes all 1,849 target
queries and both scalar recoveries using a separate finite-field group law.
`SEAL.sha256` seals the complete artifact set.
