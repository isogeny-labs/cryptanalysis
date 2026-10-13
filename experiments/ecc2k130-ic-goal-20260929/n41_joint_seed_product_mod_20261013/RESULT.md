# One target-conditioned GCD rejects all left seed families

**A reusable product of the 63 N41 left seed-family polynomials replaces 63 per-family GCDs with one target-conditioned GCD per right seed.** On a frozen eight-case panel, all decisions matched the individual-family checks and the known positive root. A seed-first search with neither seed nor output coordinate pinned found that residual witness after 20 GCD decisions. Replacing its 63-GCD hit localization by exact evaluation at the returned root reduced localization from **22.690 to 0.202 seconds** in the two recorded runs. Independent checked Sage replay verified the selected two raw points sum to the frozen residual and project to the archived pair witness.

This is an exact **two-free-pair residual** method on `EC1N41Ckb1h7d5e80d3c4d0`, `GF(2)[t]/(t^41+t³+1)`, `y²+xy=x³+1`, subgroup order `549756390943`. Its source is the W6 seed-sum family at Frobenius rotations 20 and 30, with projected base size `B=256` and 26 folded columns. The positive residual is a preexisting constructed correctness control; the negative residual is its frozen control partner. The four raw preimages of each are derived by checked Sage. This component has `candidate_id: null`.

## Exact family gate

For left seed `s`, let `F_s(Z)` be the archived degree-64 pair-output polynomial, and set `L(Z)=∏_{s=1}^{63}F_s(Z)`, degree 4,032. For a right seed `t` and raw target lift, the archived linearized recurrence computes target-conditioned norm `N_t(Z)`, degree at most 128. The gate is

`gcd(N_t, L) ≠ 1`.

Equivalently, multiply the 63 `F_s` **modulo** `N_t` and GCD the residue with `N_t`. Every root in the base field is a compatible left output for at least one seed family; testing `F_s(root)=0` identifies those seed labels without another GCD. Because a genuine left family root also zeros `L`, the reduction rejects no genuine algebraic family hit. The [Lean theorem](FamilyGate.lean) proves the modular-product zero criterion under evaluation-preserving reduction and no-zero-divisors assumptions. The concrete polynomial-remainder, resultant, field, and curve bridges are checked by the frozen panel and independent Sage replay and listed in the [proof map](PROOF_MAP.md).

## Frozen panel and seed-first search

The [first protocol](protocol.json) fixed eight positive/negative raw-lift and right-seed cases, source hashes, one checked Sage worker, a 180-second cap, and 4 GiB. Three cases also ran all 63 individual GCDs. The [global-product protocol](global_protocol.json) then paired those exact cases with one reusable `L`; every GCD degree agreed. The [seed-first protocol](search_protocol.json) fixed right seeds `1..63` and raw lifts `0..3` before search; the algorithm read no known seed or output witness. A revised [search protocol](search_v2_protocol.json) changed only localization after a hit. The same [Sage runtime receipt](sage_runtime_info.json) precedes all local Sage jobs.

| Exact stage or exploratory interval | Result |
| --- | ---: |
| Eight panel decisions / individual-family checks | 8/8 matched; 3/3 full 63-GCD checks matched |
| Median target-conditioned modular-product plus GCD, eight cases | 2.279 s |
| Median target-conditioned GCD with reusable global `L`, same cases | 1.300 s |
| Individual 63-GCD checks, three paired cases | 18.220–26.148 s |
| Reusable global product build, paired panel | 2.680 s target-independent |
| Seed-first first hit | right seed 5, raw lift 3, left seed 16, reciprocal `585190544792` |
| First search, full runner / localization | 55.600 / 22.690 s |
| Root-evaluation search, full runner / localization | **28.024 / 0.202 s** |
| Root-evaluation search sampled peak RSS | 346,603,520 B |

The root-evaluation run's exclusive recorded phases are 1.445 s source setup, 2.747 s global-product build, 0.610 s target projection, 0.466 s norm construction, 22.548 s GCD decisions, and 0.202 s localization; the 0.006 s remainder is process bookkeeping and sampling. These CPU times are algorithmic diagnostics on an unisolated host. The deterministic improvement is replacing 63 hit-localization GCDs by 63 polynomial evaluations at one exact root. The [first independent group audit](audit_result.json) recomputed the seed-family polynomials and right roots and verified the raw point sum; the [revised checked-Sage audit](audit_v2_result.json) checked the identical hit and group sum independently of the revised search code. The [read-only receipt audit](verify.py) binds all source, protocol, output, and proof receipts.

The reusable N41 `L` is nearly dense: the [exact coefficient census](sparsity_result.json) found **4,007 nonzero coefficients out of 4,033**, with every nonzero coefficient retained in [nonzero_coefficients.json](nonzero_coefficients.json). The earlier [full-domain inverse join](../n41_linearized_full_bucket_scan_20261011/RESULT.md) already classifies all eight residual lifts by target-conditioned roots after reusable setup. The present seed-first run stops at the first positive residual hit; it does not replace that complete coverage control.

## N131 transfer gate and next construction

For the literal unfiltered W18 analogue over `GF(2)[t]/(t^131+t^13+t²+t+1)`, each nonzero seed gives a degree-`2^18` bucket polynomial and there are `2^18−1` seeds. Since products of two `span(t,…,t^18)` elements have degrees 2 through 36, the coefficient `p=1` is absent and the leading quadratic term does not vanish. The resulting global product has exact degree **68,719,214,592**. A dense 131-bit coefficient array needs **1,125,277,138,961 bytes**; even one bit per coefficient needs **8,589,901,825 bytes**. The literal four-raw-fiber scan also requires **1,048,572 right-seed GCD decisions**, at least 1,748/s to finish in 600 seconds before setup and hit localization. The [projection protocol](projection_protocol.json), [exact result](projection_result.json), and receipt auditor preserve this representation-specific gate. N41 coefficient density is an observed control, not an asserted N131 density theorem.

The next algorithm must evaluate the **global left-family zero predicate implicitly**, without building that polynomial or enumerating every seed. The strongest existing N131 building block is the [single-output W18 product-span inverse](../n41_n131_universal_product_linearized_20261011/RESULT.md), which checks a proposed pair coordinate by one 19-variable binary solve. The missing step is to derive a compact family of such coordinates jointly from the public target and at least two unresolved partial sums. An unpinned N41 public-point relation and a source-bound N131 one-worker 600-second/4-GiB query remain the promotion gates.

All local Sage jobs were launched through the repository's checked `./sage -python` launcher after `./sage --runtime-info` was saved. From the repository root, the read-only receipts replay with `python3 -B experiments/ecc2k130-ic-goal-20260929/n41_joint_seed_product_mod_20261013/verify.py`; the formal module builds with `lean FamilyGate.lean` from this directory.
