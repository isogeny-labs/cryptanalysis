# T-1299 independent source-to-claim fidelity review (preliminary)

Reviewer joint ownership: **J1, J3, J4**. Verdict: **holds at the stated algebraic scope; broader concrete and cost bridges remain inconclusive**. Sibling report access: **no**. This report was written without opening `/var/tmp/cryptanalysis-known-label-blind-review-20261101.md` or communicating with its reviewer. No blind re-derivation is claimed here; J2 is assigned to the blind reviewer. No repository or official ledger file was changed.

## Pins and machine evidence

- Producer commit: `52baa40a94751916c0d8b83ec8691125bccdac3c`.
- `docs/known-label-next-leads-20261028/Algebra.lean`: independently recomputed SHA-256 `d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d`.
- `docs/known-label-pair-index-20261029/PairIndex.lean`: independently recomputed SHA-256 `68dd10106b5499ad8b3fba35b95980a5ed1e6c46c0433047e0d5034e90c135c8`.
- Published plan: `b182f5c4cb6f1dcddbf83523d3abd03bed515afe:docs/known-label-pair-index-20261029/review-20261101/review_plan.md`.
- Hosted [corpus run 41344355706](https://github.com/isogeny-labs/cryptanalysis/actions/runs/41344355706), successful on CI head `6ad8b68d8d79bb31e8f915915f844796344d8b57`. Its log shows native compilation, full names, `#print axioms`, exhaustive `ok` records, 4/4 and 7/7 summaries, and native `#check @...` elaborated type output. CI head differs from producer pin; the gate's fixed source hashes and log bind the two reviewed source bytes. This reviewer did not execute a new Lean build.
- The gate's project pins are Lean `v4.35.0-rc4`, Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`; it checks source, auditor and three project input hashes, a fresh compiled object, exact names and theorem count, allowed transitive axioms, then rechecks source/object. The hosted log lists only `propext`, `Classical.choice`, and `Quot.sound` among these eleven declarations; zero failing or trusted exceptions. These are native CI machine observations, not an independent binary/kernel recheck.

## Per-claim preliminary findings

`passed` below means the named hosted native source-bound check passed. `partial` means the Lean statement supports the algebraic portion but does not establish its concrete or executable use. `needs_revision` requests a narrower proof label or a missing bridge, not a claim that the displayed identity is false.

| Declaration | Exact type/claim boundary checked | Machine | Fidelity | Outcome |
| --- | --- | --- | --- | --- |
| `KnownLabelLeads.triangle_identity` | All `a b c` in any commutative ring; `2*a=(a+b)-(b+c)+(c+a)`. No edge-verification or invertibility premise. | passed | faithful_scoped | validated_scoped for ring identity |
| `KnownLabelLeads.signed_second_moment` | Ring polynomial identity yielding `2(a-c)(b-c)`; division by 2 and distinct-index/nonzero denominator lie outside its type. | passed | faithful_scoped | validated_scoped for identity |
| `KnownLabelLeads.signed_third_moment` | Ring polynomial identity yielding `6c(a-c)(b-c)`; no decoder correctness or unique-index theorem. | passed | faithful_scoped | validated_scoped for identity |
| `KnownLabelLeads.positive_pair_product` | Ring identity for `2ab`; no quadratic root, bounds or signature injectivity theorem. | passed | faithful_scoped | validated_scoped for identity |
| `KnownLabelPairIndex.affine_composition` | All field modules; equality for one affine composition. No graph edge constructor. | passed | faithful_scoped | validated_scoped for abstract equality |
| `KnownLabelPairIndex.affine_path` | Fold invariant for arbitrary `List (K × V)`, initial `a • z+c`; list entries are not certified relations. Empty list is valid and proves only the identity fold. | passed | partial | needs_revision if cited as verified path construction |
| `KnownLabelPairIndex.cycle_constraint` | Assumes `h: z=a • z+c`; concludes `(1-a) • z=c`. Does not construct `h` from a closed verified walk. | passed | partial | needs_revision for graph use |
| `KnownLabelPairIndex.cycle_recovery` | Adds `a ≠ 1` over a field and the fixed-point equality; obtains `z=(1-a)⁻¹ • c`. For `a=1`, recovery is unavailable. | passed | faithful_scoped | validated_scoped for conditional module recovery |
| `KnownLabelPairIndex.label_recovery` | Assumes `gamma ≠ 0` and `gamma • z=a • p+b • q`; obtains the coefficient expression. It does not show the equality or nonzero gamma for actual elliptic points. | passed | partial | needs_revision for concrete label recovery |
| `KnownLabelPairIndex.signed_square` | Assumes four recurrences, including `r0=r3-t30`; proves doubled-root formula. It does not obtain those recurrences from checked signed edges. | passed | partial | needs_revision for executable graph use |
| `KnownLabelPairIndex.semaev_pair_identity` | Field polynomial identity under two on-curve equations `u²=x³+ax+b`, `v²=y³+ay+b`; cleared formula only. It does not assert `x≠y`, point group addition, factorization into the two actual signed-sum abscissae, H coverage, or index completeness. | passed | partial | needs_revision for pair-index correctness claim |

The native `#check` output agrees with the displayed source hypotheses: `CommRing K` for the first four, `Field K`, `AddCommGroup V`, `Module K V` for the module statements (unused parameters are elided by Lean for individual declarations), and `Field K` plus the two curve-polynomial premises for `semaev_pair_identity`. No theorem above quantifies over a concrete elliptic curve, `ZMod r` subgroup points, a Python output, field-operation cost, or a probability space. The algebraic assumptions are nonvacuous (for example, `K=ZMod 101`, `V=K`), but this does not discharge concrete curve premises.

## J1: exact name and trust attacks

The pinned gate names all eleven fully qualified declarations in `KNOWN_LABEL_THEOREMS` and `PAIR_INDEX_THEOREMS`, checks the exact source hashes, requires the same `#print axioms` name inventory, and requires those names in the exhaustive module audit. A source rename/removal changes the pinned hash; a forged/missing native name fails the exact-name comparison. `test_current_corpus_gate.py` contains simulated controls for a missing fourth audit, missing seventh audit, other-namespace names, missing/duplicated type headers, a custom `ClaimAsAxiom`, `sorryAx`, and empty/failing audits. The hosted run additionally exercised native positive, custom-axiom, empty-audit, and ill-typed refusal fixtures. These controls support gate behavior; simulated output does not authenticate a proof. I found no missing or renamed named declaration in the pinned files. The source scan also rejects `sorry`, `admit`, `sorryAx`, `native_decide`, and `axiom` before compilation.

## J3: concrete bridge and exceptional cases

The producer defines a verified edge as an actual equality `R_i+s R_j = t([a]P+[b]Q)` with finite subgroup points and a prime order `r>3`. None of the eleven Lean theorems constructs a `ZMod r` module on this concrete subgroup, defines `R_i`, `P`, `Q` as points, or turns a checked edge into `z=a • z+c`. Required steps are: (1) validate curve/point/subgroup/order and orientation; (2) interpret scalar pairs modulo `r` and prove the point-group module action; (3) prove each oriented signed edge transports a point and a two-coefficient expression, including the reverse edge; (4) construct the path and cycle fixed-point equality from checked edges; (5) prove the recovery coefficient is nonzero for the chosen signed cycle, then replay the recovered label in the curve group. The README describes these steps and labels them unformalized; the Lean claims do not silently supply them.

The characteristic-two attack is concrete: the ring triangle identity still says `0=0` after doubling, so it cannot recover `a` by division by two. The module theorem requires `a≠1`, which excludes a balanced all-sum even cycle (`a=1`). A trivial module or empty graph satisfies abstract equalities without constructing labels. The signed square is a valid even-cycle algebra example with an unbalanced sign product; parity alone is not the criterion. The field theorem for the cleared pair polynomial has no `x≠y` and cannot alone justify division by `(x-y)²`; the README explicitly imposes distinct abscissae, odd prime subgroup order and finite/nonzero signed sums.

## J4: executable relation and cost bridge

At pinned bytes, `pair_index.py` builds one quadratic `F_ij` per distinct input abscissa pair, a product tree, batched remainder evaluation, and a zero-branch descent returning every matching leaf. `signed_witnesses` then computes both actual `R_i±R_j` once per pair, checks a unique sign match against `±T`, and returns graph edges and identity candidates. `signed_labels.py` propagates signed affine offsets and emits coefficient defects. The test fixture supplies curve operations, a known secret only to construct/replay labels, enumerates all finite targets on the p=827/r=823 fixture, compares localized pairs with independent point enumeration, and replays recovered labels; archived `CHECKS-attempt3.json` records ten passing deterministic controls. Thus there is an executable finite-fixture relation check, but no Lean-to-Python equivalence theorem or untrusted-input certificate API.

The executable API relies on caller-supplied curve points, subgroup order, target labels and group operations. It checks distinct x values and point x alignment, but does not itself validate primality, on-curve/subgroup membership, target-label replay or the final DLP candidate. An identity-target `candidate_d` and zero-relation coefficient pair are outputs requiring external independent verification. The README and protocol explicitly reserve these checks for a complete driver. Consequently the deterministic fixture validates one supplied curve/model and does not establish arbitrary-input correctness.

The cost statements in the README are derived soft field-operation bounds: degree `D=n(n-1)`; product/remainder trees and one batch `O~(n²+N+C)` field operations and storage with `C` returned pair/target incidences. Zero-only descent visits at most a logarithmic number of ancestors per returned incidence, so the stated output-sensitive localization accounting is plausible at this abstract operation level. The Lean file proves no complexity theorem, and neither the fixture nor CI measures these costs. No complete constructor driver, charged point lifting/filtering and scalar replay, memory/wall-time benchmark, or matched dictionary/BSGS comparison is in the reviewed evidence. Treat the cost as a written model, not measured improvement.

## Controls executed here and limits

I extracted the pinned Python sources to a temporary `/var/tmp/known-label-fidelity-*` directory. The full unit suite could not run locally: `python` is absent; `python3` exists but this environment lacks `sympy` (import error before tests). I did run dependency-free `signed_labels.py` with Python 3: an empty graph returned no labels; an all-sum even square returned one unresolved component and no labels; the unbalanced three-sum/one-difference square returned four labels; order 2 was rejected with `ValueError`. These are local behavior controls, not an independent curve proof. The archived ten-test receipt is producer evidence, separately described above. No heavy build or new benchmark was run.

## Attestation and sources_read

`joints_owned: [J1, J3, J4]`; `sibling_report_access: no`; `blind_rederivation_compliance: not applicable to this assigned source-fidelity role`; `verdict: holds` **for the exact four ring and seven abstract identities at their hypotheses**, with `inconclusive` concrete graph-to-module, executable-generalization and cost bridges. No claim of J2 independent derivation is made.

`sources_read` (exact paths or hosted record):

- `/var/lib/spot-codex/home/skills/review-evidence/SKILL.md` and `references/lean-review.md`;
- `b182f5c4:docs/known-label-pair-index-20261029/review-20261101/review_plan.md`;
- `52baa40a:docs/known-label-next-leads-20261028/{Algebra.lean,README.md,CI_INTEGRATION.md}`;
- `52baa40a:docs/known-label-pair-index-20261029/{PairIndex.lean,README.md,PROTOCOL.md,pair_index.py,signed_labels.py,test_pair_index.py,CHECKS-attempt3.json}`;
- `52baa40a:tools/lean/{current-corpus-gate.py,test_current_corpus_gate.py,README.md}`;
- `/home/ec2-user/cryptanalysis/AGENTS.md`;
- GitHub Actions run `41344355706` metadata and filtered native corpus/audit/type/refusal log lines.

The sibling report path named above was **not read**. This preliminary report can be reconciled with J2 only after both reports are filed.
