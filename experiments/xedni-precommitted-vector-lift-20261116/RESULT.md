# Precommitted vector lift acceptance equals the public relation event

A deterministic vector-dependent rank-one lift rule, fixed before fresh public queries and applied to **all 6,656 selected attempts**, accepted exactly the **121** attempts with a public group relation. The rule constructs a rational curve and an automatic rational relation on every attempt; its second point reduces to the required public point exactly when the public relation holds. All 6,535 selected mismatches remain recorded. Thirty-two planted relation controls passed, and 32 nearby negative controls failed. A checked Lean theorem establishes the abstract acceptance equivalence, while an independent Python replay checked every finite and rational point computation and every accepted scalar.

## Frozen input and construction

`protocol.json` pins the eight-field generator registry and the 13 selected vectors by SHA-256 before measurement. For each field it fixes four new target scalars using SHA-256 of `xedni-precommitted-v1|p|j`, builds the public point Q=wG, and selects the first 16 admitted ordered offset pairs from `[0,1,2,3,5,8,13,21]`. Fixture construction is outside the attempt phase. The complete selected workload is 8 fields × 4 targets × 16 queries × 13 vectors = 6,656 attempts. The separate `(1,2)` positive and negative controls add 64 attempts.

For each vector `(a,b)` and public pair `U=Q−t₁G`, `V=Q−t₂G`, the rule computes `T=b⁻¹U` in the finite subgroup **without first testing** `aU+bV=O`. It centers the coordinates of T as integers `(x,y)`, sets `B=y²−x³+x`, and takes `P=(x,y)` on `E_B/ℚ: y²=x³−x+B`. It then constructs `A=bP`, `C=−aP`. The rational relation `aA+bC=O` holds by construction. Acceptance requires both reductions `A↦U` and `C↦V`; the public relation is computed afterward as a separately recorded diagnostic.

| Arm | Attempts | Accepted | Rejected | Public relations |
| --- | ---: | ---: | ---: | ---: |
| Selected 13 vectors | 6,656 | 121 | 6,535 | 121 |
| Planted `(1,2)` positive controls | 32 | 32 | 0 | 32 |
| Shifted-offset negative controls | 32 | 0 | 32 | 0 |

Every attempt constructs one rational model, computes one finite preimage scalar multiplication, two rational point multiples for `A,C`, the rational relation check, two reductions, and the public diagnostic. This is an exact stage-operation boundary, not an isolated wall-time comparison. `rows.jsonl` retains field, subgroup, target fixture, query offsets, public points, vector, common finite point, rational curve parameter, rational points, reductions, diagnostics, and status. Accepted selected rows have independently replayed target scalars; controls are reported separately from selected yield. The checked local Sage build is recorded in `sage-runtime.json`.

## Proof and formalization map

The structural theorem assumes an additive reduction homomorphism `reduce`, a point `P`, public points `U,V`, integers `a,b`, the first-image condition `b • reduce(P)=U`, and injectivity of multiplication by `b` on the finite target group. It states that `reduce(−a • P)=V` if and only if `a • U+b • V=0`. Here `b` is nonzero modulo each prime subgroup order, so the injectivity condition holds. The public relation also gives scalar recovery from `(a+b)w=a t₁+b t₂` whenever `a+b` is invertible, as checked for every accepted event.

| Result | Lean declaration in `formal/PrecommittedVectorLift.lean` | Status |
| --- | --- | --- |
| Automatic rank-one rational relation | `precommitted_rank_one_relation` | checked |
| Second reduction match iff public relation | `precommitted_second_reduction_iff_public` | checked |
| Both reductions match iff public relation | `precommitted_acceptance_iff_public` | checked |
| Instantiate on every named rational elliptic curve and its good reduction | no Lean declaration | partial formalization; exact arithmetic replay and written proof retained |

The pinned Lean 4 toolchain is `v4.35.0-rc4` with Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build PrecommittedVectorLift` completed 9,040 jobs. The `#print axioms` audit lists only standard `propext` and `Quot.sound`; `lean4checker --fresh` was unavailable. The remaining formal bridge is construction of the actual rational elliptic-curve reduction homomorphism and formal checking that it maps the named point to the saved finite point. The theorem keeps these as explicit hypotheses and does not assume the public relation.

`audit.py` uses independent pure-Python finite and rational short-Weierstrass group laws. It reconstructs all targets and ordered queries from the frozen source hashes, replays all 6,720 curve and point computations, checks the rational relation and both reductions, and independently replays every accepted scalar. Its `PASS` receipt is `audit.json`.

The result pinpoints the cost of this precommitted rank-one rule: constructing a rational relation is unconditional, while matching the second public point is the same event as the public group relation. A next construction must supply a lift of both public points before this equivalent relation work, with its selection and rejection cost recorded.

## Reproduction

From the repository root:

```sh
./sage --runtime-info
./sage -python experiments/xedni-precommitted-vector-lift-20261116/run.py
python3 experiments/xedni-precommitted-vector-lift-20261116/audit.py
```

From the experiment's `formal` directory, run `lake build PrecommittedVectorLift`. `SEAL.sha256` fixes the protocol, source, raw rows, reports, build, runtime, and audit receipts.
