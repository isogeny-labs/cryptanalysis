# N41 joint-pair filter experiment

## Contribution

The diagonal two-pair source affinely spans the trace-zero reciprocal space for **every** ordered pair of nonzero source seeds. An independent field-arithmetic replay checked 41 pivotal witnesses in each of the 65,025 seed bins. Consequently, an output-only affine parity filter conditioned on those two seeds has no additional exact gate beyond reciprocal trace zero. A second census reaches the full 821-dimensional space of degree-at-most-two Boolean functions in all 255 equal-seed bins, and an independent arithmetic path reproduces every rank and probe count. This redirects the next filter experiment toward a condition using both partial sums and the public target, rather than a low-degree test of one combined reciprocal.

## Exact source and result

The finite source is the frozen `EC1N41Ckb1h7d5e80d3c4d0` diagonal source in `../n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv`. Its field representation is `GF(2)[z]/(z^41+z^3+1)`; `trace_mask=1` in the independent replay, so the coefficient of `z^0` is the absolute trace. Slots 0 and 1 use Frobenius rotations 0 and 7. Each signed pair state has two folded columns and source-seed label `a XOR b`. The enumerator admits a two-state sum only when its four folded columns are distinct and the output x-coordinate is nonzero. Its feature is the reciprocal of that x-coordinate. The exact source and input hashes are in `rank_protocol.json` and `quadratic_protocol.json`. These are finite source-law studies; the IC candidate ID remains `null` because a complete N131 pipeline is not specified here.

| Experiment | Frozen feature and scope | Complete result | Independent check | Resource record |
| --- | --- | --- | --- | --- |
| Affine | `(1,c_0,...,c_40)` for all 255×255 seed pairs | Rank 41 in all 65,025 bins; 2,771,278 checked pair sums and 2,666,025 saved pivotal witnesses | `audit_rank.cpp` recomputed every pivot using full-product GF(2^41) arithmetic, batch inversion, and low-pivot elimination; `PASS_INDEPENDENT_FULL_RANK_REPLAY` | Producer 3.236 s, 36.3 MB sampled combined RSS; replay 4.623 s, 45.4 MB; one worker, 180 s/4 GiB cap |
| Degree two | All 821 square-free monomials of degree 0, 1, or 2 in the 40 free reciprocal bits, for all 255 equal-seed bins | Rank 821 in every bin; 390,762 checked sums | `quadratic_audit.cpp` recomputed all 255 rows with independent field arithmetic and opposite pivot order; `PASS_INDEPENDENT_QUADRATIC_REPLAY`, including exact probe counts | Producer 1.919 s, 35.6 MB sampled combined RSS; replay 2.138 s, 35.9 MB; one worker, 180 s/4 GiB cap |
| Public trace-projected N41 query | Six trace-zero unit clauses added to the exact four-pair circuit for frozen public preimage 1 | Formula has 14,803 variables, 35,810 clauses, 2,892 native XOR rows; constructed positive assignment checks all rows | CryptoMiniSat terminated by parent wall cap at 190.026 s: `BOUNDED_UNKNOWN`, 301.1 MB sampled combined RSS | One worker, 180 s solver/190 s parent/4 GiB; `solver_receipt.json` retains the capped attempt |

The elapsed times are local algorithmic diagnostics, not isolated CPU speedup measurements. Source preparation, solver startup, target computation, final relation rank, and target scalar recovery are separate pipeline stages. The frozen N41 public point and complete formula details are in `formula_result.json`; the positive N41 relation and folded rank are independently replayed in `../n131_w18_allseed_fourpair_20261012/n41_diagonal/audit_result.json`.

## Mathematical conclusion and proof

Let `V` be the 40-dimensional GF(2) kernel of the absolute trace in GF(2^41). Fix source seeds `(s,t)` and let `C_(s,t)` be the reciprocal x-coordinates of admissible sums of one slot-0 and one slot-1 pair state. The affine census supplies 41 elements of `C_(s,t)` whose rows `(1,c_1,...,c_40)` have rank 41. A Boolean affine function of the free reciprocal coordinates that vanishes on `C_(s,t)` vanishes on these 41 rows. Its 41 coefficients therefore solve an invertible homogeneous system and are zero. This holds for every `1 ≤ s,t ≤ 255` in the frozen source.

For each equal-seed bin `(s,s)`, the second census supplies 821 rows of evaluations of all square-free monomials of degree at most two in the free 40 coordinates. Their rank is 821, the full dimension `1+40+40·39/2`. A polynomial of degree at most two vanishing on that bin must therefore have zero coefficient vector. The finite statements use the archived enumerator and an independent replay of the exact rank evidence; they do not infer an unmeasured N131 rank.

`AffineSpan.lean` proves the structural implication that a binary-linear test constant on a sampled affine spanning set is constant on its affine span. The proof applies XOR linearity to every anchor difference, then to their XOR sum. `lean_check.txt` records a build with pinned Lean 4.34.1 and the `#print axioms` audit. The finite GF(2^41) source and rank certificates are not yet imported as Lean objects; `PROOF_MAP.md` identifies that remaining bridge.

## Next experiment

The direct follow-up is a joint target-conditioned filter on the two two-pair outputs `(u,v)` and the frozen public target `T`. Freeze a predicate before measurement, prove that it preserves every valid four-pair decomposition, and measure its rejection rate on ordinary source-law pairs together with construction, lookup, and verification costs. A candidate worth advancing must reject large families before their Cartesian product is enumerated and then improve verified ordinary-relation yield per charged query. The current public SAT cap and the N131 four-pair circuit remain the comparison inputs.
