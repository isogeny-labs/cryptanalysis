# CT171: original 48-cohort native-pricing coverage gate

Date: 2026-11-16. Scientific standing: **[pcc:unverified]**. This is a source-only coverage preflight, **not** a new timing, solver, mathematical attack, signed PCC verdict, or admission to spend.

## Primary evidence inspected

- The actual committed CT125 optimized **48 selected-call rows**, frozen at Git blob `9ac741668dd1ffa9632ff0d58e6c4dd9f2dd18c3`: [literal-selected-vectors.json](../evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json).
- Its original CT82 48-row counterpart from pinned crypto commit `4de29a113dfc1b9d32c1809820b8caa2975042a8`, blob `19bc5c1ad37d55daa51a9ec95fa0af90296385c6`, read separately. [Original fixture](https://github.com/isogeny-labs/crypto/blob/4de29a113dfc1b9d32c1809820b8caa2975042a8/research/chained_jacobian_transfers_20261110/evidence/public-n4-complete-chain-checkpoint-01/01-literal-setup-and-selected-vectors.json).
- The actual CT126 Rust primitive benchmark, blob `ac4146577f5019fc17674deb342eb5d9fc749715`: [src/main.rs](src/main.rs). The owned [CT141 admission protocol](CT141_ADMITTED_NATIVE_PROTOCOL.md) already limits it to five public scalars; this continuation quantifies the missing original-cohort classes rather than duplicating the measured primitive experiment.

Both frozen 48-row records contain precisely **two directions × four cofactor sectors × six scalars** = 48 distinct inputs and 48 distinct outputs. The scalars are `0, 1, 2, 17, 12345, 2771710`; each direction/sector cell has one instance of each. The 48 optimized retained-route rows split into **8 identity exceptional** cases (scalar 0: four explicit half checks and zero generic ordinate/factorizations) and **40 generic** cases (eight half checks, four generic ordinate and one generic-halving factorization). In the identity cases, exactly one infinity or two-torsion half is counted. The original direct/retained/literal map-count reductions match the published prior protocol. These are **integer-record observations only**. [pcc:unverified]

The existing CT126 Rust benchmark constructs a five-element **nonidentity** scalar panel `[1,2,17,12345,ELL-1]`, from source model 0 to target model 2 only. It runs `C169`, two `C13` maps, target doubling, direct warm and retained warm, but **does not execute 2→0, k=0, or explicitly label any cofactor sector**. Consequently its future paired ABBA microtimings cannot be promoted as a complete 48-cohort original-chain price. This is a *coverage mismatch*, not proof that CT126's arithmetic or already scoped five-point timings are wrong. No missing-sector behavior is inferred. [pcc:unverified]

## Executable preflight

`ct171_selected_coverage.py` reads **the actual committed 48-vector file**, checks its Git blob SHA and every direction/sector/scalar combination, unique ordered public inputs/outputs, norm-reuse evaluation counts, and identity-vs-generic branch counters. It simultaneously pins CT126's original Rust-source Git blob and rejects an edited sampling panel or direction instead of silently trusting stale analysis. Its `--self-test` mode makes six **mutations of the actual loaded fixture** and two CT126 source mutations, all of which must be refused. It does not rewrite either source. Run under both normal and optimized Python:

```sh
python3 -S experiments/chained-transfer-public-target/primitive-pricing-01/ct171_selected_coverage.py --self-test
python3 -O -S experiments/chained-transfer-public-target/primitive-pricing-01/ct171_selected_coverage.py --self-test
```

The separate workflow performs these bounded source-only checks at its exact PR head; a passing run does **not** verify native timing, independent 695/701 custody, or ECDLP performance. No new PCC record/ledger or artifact trust is promoted; existing source-only claims remain unverified until independent signed PCC processing.

## Decisive next admitted experiment

1. Extend the existing **Rust**, not a new Python/JS solver, to take the frozen 48 actual public inputs and report the **two directions, four sectors and zero/nonzero branch class separately**. First prove every input is admitted and every output matches both maps and the actual subgroup/norm checks; reject missing/duplicate strata. Do not silently substitute an unrelated field model or curve.
2. Run the pinned, owner/budget-admitted native \(C_{169}, C_{13a}, C_{13b},D\) paired ABBA experiment on the same isolated host, plus warm/cold setup and correction costs, A/A, per-class variability, failures and memory. Keep the present five-point CT126 probe as a separate diagnostic baseline.
3. Reproduce the whole original/reuse **695/701** corpus independently from authenticated raw custody, including all omissions. A complete source-prime ECDLP benchmark must include setup, transfers, corrections, linear algebra, verification and strongest optimized source rho/BSGS/index calculus on identical public targets. Require independently signed PCC and baseline/candidate cost ratio greater than 1; otherwise record the negative and redirect to non-generic IC.

**Blocked presently:** full original raw 123-MB comparison custody, owner admission/budget STOP for native pricing, full cold solver instances, and signed PCC. The current [research queue](https://github.com/isogeny-labs/crypto/issues/3904) and [root PR #3877](https://github.com/isogeny-labs/crypto/pull/3877) preserve those blockers. No EKS, Spot, GPU, paid benchmark, protected merge or policy waiver was performed.
