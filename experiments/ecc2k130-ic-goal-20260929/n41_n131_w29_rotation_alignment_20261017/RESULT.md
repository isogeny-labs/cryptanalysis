# Aligned five-pair Frobenius slots and their branch quotient

Pairing equal Frobenius rotations creates a **47-dimensional root-branch annihilator** in the N131 W29 five-pair source, compared with one dimension under the original rotation schedule. An exact N41 W9 public-point join found an ordinary relation with the aligned source, and independent checked Sage replayed all ten leaves and the subgroup projection. The unpinned solver gate did **not** benefit at N131: at 100,001 conflicts, the completed aligned probe made 457,056 decisions and reported about 81 million propagations, versus 413,447 and about 45 million for the original formula. The other aligned N131 probe reached its 150-second wall cap without a terminal solver status. Alignment without an explicit target-conditioned quotient constraint is therefore not selected for a 600-second public query.

## Source geometry and exact branch rank

Both instances use `E: y²+xy=x³+1`. N41 is `GF(2)[u]/(u^41+u³+1)` on `EC1N41Ckb1h7d5e80d3c4d0`, seed mask 56, 71 canonical W9 pair edges, and 284 signed states per slot. N131 is `GF(2)[u]/(u^131+u^13+u²+u+1)` on `EC1N131Ckb1heb5f1998f20b`, seed mask 898618 and 28 free canonical W29 bits. The same frozen public subgroup point is used within each field comparison. All five slots retain the same pair source and distinct folded-column policy; only their Frobenius rotations change.

For canonical source element `a` and fixed seed `s`, the pair product is `p=a(a+s)=a²+sa`, a binary-linear function of the source code. Let `H=halftrace(s)²` and `C=1+H`. The two distinct roots of the fixed-seed reciprocal pair equation `Cz²+pz+H=0` differ by `p/C`. After slot rotation `r`, their difference lies in `U_r=Frob^r(Im(p/C))`. Equal rotations repeat this subspace. The [producer](branch_rank_result.json) and an independent checked-Sage [matrix audit](branch_rank_audit.json) obtained these exact binary ranks:

| Field | Rotation schedule | Prefix ranks across five slots | Final span rank | Annihilator dimension |
| --- | --- | --- | ---: | ---: |
| N41 W9 | original `(0,6,12,18,24)` | `8,16,24,32,40` | 40 | 1 |
| N41 W9 | aligned `(0,0,12,12,24)` | `8,8,16,16,24` | 24 | **17** |
| N131 W29 | original `(0,18,36,54,72)` | `28,56,84,112,130` | 130 | 1 |
| N131 W29 | aligned `(0,0,36,36,72)` | `28,28,56,56,84` | 84 | **47** |

The Sage audit also checked the two-root difference on every one of the 71 N41 W9 source edges. These annihilators remove variation between pair-root branches in a *linear projection of the five reciprocal output coordinates*. The final point-sum condition is nonlinear, so this rank gain alone is not a target filter.

## Frozen N41 ordinary relation and circuit control

The [N41 protocol](n41_protocol.json) freezes the transformed 1,420-state input, native source and binary, checked Sage runtime, the original raw public point `(2026560328086,1928332930914)`, all 41 target Frobenius orientations, one worker, 600-second parent wall cap, and 4-GiB worker RSS cap. The native three-plus-two join found its first hit at orientation **6**, state IDs `(105,244,66,47,111)`, after 201.569 worker seconds and 210.686 parent-wall seconds. Sampled worker peak RSS was 1,277,870,080 bytes. The independent [group audit](n41_audit_result.json) rebuilt ten source leaves, verified the fixed-seed pair quadratic, ten distinct folded columns, inverse Frobenius transport, the raw point, and its fourfold subgroup projection.

The aligned relation lies inside the reciprocal S3 circuit's nonexceptional chart. Checked Sage reconstructed its five pair-output reciprocals and three middle reciprocals in the [model fixture](n41_model_fixture.json). The aligned exact-source trace formula passed a complete assignment check of **45,734 clauses and 2,681 native XOR rows**. Since slots 0 and 1 share one rotation and slots 3 and 4 share another, each pair can be permuted while preserving the five-point sum. The verified relation also satisfies strict source-code ordering `code₀<code₁` and `code₃<code₄`; the ordered formula passed all **45,868 clauses and 2,727 XOR rows**. Code equality would repeat both endpoint columns for this source, so the strict ordering removes only duplicate permutations of admissible distinct-column witnesses.

The [matched N41 probe](probe_n41_result.json) uses the same oriented public point in all three formulas, one CryptoMiniSat worker, a requested 50,000-conflict cap, a 90-second parent cap per run, 4-GiB combined RSS cap, and order `original, aligned, ordered, ordered, aligned, original`. All six runs returned `INDETERMINATE` at 50,001 conflicts. The exact deterministic counters repeated in reverse order:

| N41 formula | Decisions | Reported propagations | Parent wall readings |
| --- | ---: | ---: | --- |
| Original rotations | 83,981 | 17.327M | 21.117, 25.862 s |
| Aligned rotations | 83,739 | 17.082M | 19.870, 24.105 s |
| Aligned with strict code order | 91,718 | 17.661M | 23.473, 20.463 s |

Alignment reduced this fixed-work propagation counter by about 1.4%; the additional ordering increased it. These are source and solver diagnostics on a shared host, not relation-yield or calibrated wall-speed results.

## N131 constructed control and public solver gate

The independent [N131 constructed control](n131_aligned_control.json) transported the five archived checked pair points to rotations `(0,0,36,36,72)`, recomputed all three middle sums and a new constructed target, and retained ten distinct folded columns. Its exact aligned trace circuit passed every **232,430 clause and 41,956 native XOR row**. The public [aligned formula](build_n131_result.json) uses the *original frozen N131 public point* and has 76,859 AND gates, 120,658 variables, 232,430 clauses, and 41,956 XOR rows. The original trace formula on that point has the same AND/ordinary-clause counts, 121,205 variables, and 42,503 XOR rows.

The [N131 probe protocol](probe_n131_protocol.json) pins both public formulas, solver binary, checked Sage runtime, one worker, 100,000 requested maximum conflicts, 150-second parent cap per run, 4-GiB combined RSS cap, and order `original, aligned, aligned, original`. Raw solver output and the [result receipt](probe_n131_result.json) preserve every run:

| Order | Rotation schedule | Terminal status | Conflicts | Decisions | Reported propagations | Parent wall | Peak combined RSS |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | Original | `INDETERMINATE` | 100,001 | 413,447 | 45M | 56.884 s | 103,415,808 B |
| 1 | Aligned | `WALL_CAP`; no terminal solver status | last flushed restart near 93K | unknown | unknown | 150.053 s | 130,564,096 B |
| 2 | Aligned | `INDETERMINATE` | 100,001 | 457,056 | 81M | 141.431 s | 166,543,360 B |
| 3 | Original | `INDETERMINATE` | 100,001 | 413,447 | 45M | 53.081 s | 113,082,368 B |

CryptoMiniSat rounds propagation counts in its terminal output. The completed aligned arm required approximately **1.8 times** the reported propagations and **1.105 times** the decisions of the original at the same conflict boundary. The first aligned arm is censored, not a zero-yield or UNSAT result. Shared-host wall readings are descriptive. This gate provides no reason to spend the full N131 public-query cap on the unchanged aligned formula.

## Quotient-label cost and proof map

The common N41 annihilator yields 17 root-branch-invariant one-bit labels for slot zero. An exact screen over all 71 source codes found **no affine or quadratic Boolean expression in the eight canonical code bits** for any of those 17 labels. Independent checked Sage built the 71×37 degree-at-most-two feature matrix, found rank **37**, and found augmented rank **38** for every label. Degree-three features have rank 71 on these 71 codes, so their fits are full interpolation and do not establish compact formulas. This is an early cost test for exposing slot-zero quotient bits to a source-code solver, not a degree claim for other slot rotations or N131. The [screen](quotient_label_result.json) and [audit](quotient_label_audit.json) retain all masks, labels, and ranks.

[AlignedSymmetry.lean](AlignedSymmetry.lean) builds under pinned Lean 4.34.1; [output](lean.stdout) and `#print axioms` show only standard Lean foundations (`propext`, `Classical.choice`, `Quot.sound`) and no `sorry`, `admit`, or `sorryAx`. `ordered_pair` proves strict ordering preserves an equal-rotation pair sum given distinct codes. `two_pair_swaps` proves the balanced five-point sum is invariant under the two independent slot swaps. `pair_root_difference` proves the quadratic two-root difference over a characteristic-two field with invertible `C` and distinct roots. The exact N41/N131 finite-field rank and N41 Boolean-degree exclusions are independently computed and checked, but their concrete modulus/matrix certificates are not yet formalized in Lean; those bridge obligations remain open. `lean4checker --fresh` was unavailable on this host.

The initial system-Python builder invocation stopped at a transitive `psutil` import before formula construction; [preflight receipt](preflight_failure.json) records that environment outcome. All completed local Sage work used the checked repository `./sage` launcher with the saved [runtime receipt](sage_runtime_info.json). The [terminal verifier](verify.py) binds protocol, input, formula, raw output, group audit, matrix audit, model checks, probe statuses, and Lean output. The stage configuration retains `candidate_id: null` because exact W29 factor-base enumeration, useful relation rank, final linear algebra, target descent, and a paired same-point rho result are not yet part of this candidate.

## Next discriminator

The geometry creates a large exact quotient but does not make the existing SAT search cheaper. The next test must use the aligned quotient in a **target-conditioned constraint on at least two unresolved partial-sum families**, with its source-code evaluation charged before branch expansion. The first gate is whether a compact predicate can be computed over whole N41 W9 code families while preserving the verified orientation-6 relation and rejecting ordinary misses; the second is a source-bound N131 projection under one worker, 600 seconds, and 4 GiB. The present rank and slot-zero degree results supply exact parameters and a concrete obstruction to an affine or quadratic slot-zero code-label implementation.
