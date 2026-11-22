# CT249 — cumulative clock reconciliation source adjudication

**Date:** 2026-11-19 America/Denver (CI 2026-11-20 UTC). **Standing:** [pcc:unverified]. **Classification:** engineering / integrity guard, not a mathematical or physical speedup.

## Change against exact CT248 source

CT248's native-record auditor required 144 epoch samples and one 48-vector event, but did **not** consume the existing generated-Rust `CT244_PRIMITIVE_TIMING` runtime-lifetime record. An apparent paired primitive delta could therefore be accepted even if the 144 per-arm samples' summed elapsed times or call counts exceeded the unfiltered lifetime measurement.

CT249 (preregistered in `CT249_CUMULATIVE_CLOCK_RECONCILIATION_PROTOCOL.md`, prior commit `9a950614044e807bfd8f74d4dcd3cb4bdcc8c6d3`) fixes the auditor, **without modifying the Rust producer**, original frozen 695/701 records, sample clocks or source geometry.

The auditor now requires exactly one native lifetime record; its precise seven ordered directed slots, schema, source/standing and 144-emission count; nonnegative typed seven-slot counts/times. For every direction it computes

`unscoped_count_j = lifetime_count_j - sum_{i=0}^{143} scoped_count_{i,j}`,
`unscoped_ns_j = lifetime_ns_j - sum_{i=0}^{143} scoped_ns_{i,j}`,

and rejects if either is negative. Actual lifetime overhead and other arms can contribute to these **nonnegative residuals**; they are not attributed to any candidate or baseline arm. Nonzero lifetime ns with zero calls is rejected. Existing per-epoch original C13/C169/D counter reconciliation and 48-row order checks remain intact.

## Actual GitHub-hosted execution

- [Exact-head source/auditor Actions run #44649552047](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44649552047), job `136000702543`: **passed** at source commit `5f793dd86698ad27bf4c61678ce81a31b082dfa5`.
- Normal Python and optimized `python3 -O -S` each output `CT249_AUDITOR_SELFTEST_PASS 31 mutations and two positive controls; no native run or cost`. Positive controls cover both nonzero outside-epoch map work and zero residual; 31 corruptions per mode include missing/duplicated lifetime events, invalid cumulative counts/times, altered slot labels/scope, wrong 144 emission count, Boolean integer alias, and fake verified/complete-solve standing.
- CT244 generator source guards also passed, separately generated Rust source parsed with rustfmt, and pinned original Rust blobs remained guarded. These checks **do not semantically compile** or execute the native evaluator.

## Negative/unknown and next decision

The [same-head read-only authentication run #44649551476](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44649551476) reported credentials present but no session token, `CT246_STS_CLASS=invalid_token`, `CT246_HEAD_CLASS=forbidden_403`; this prevents approved six-object model custody. The reason for invalid credentials is not proved. Do not substitute fixtures or treat synthetic clock reconciliation as native timing.

CT249 does not verify source-array authenticity by an independent arithmetic implementation, nor does it cryptographically prove physical execution. A malicious producer could modify both epoch and lifetime clocks consistently. Native signed PCC and independent same-host repetition remain obligatory.

**Unmet science gates:** six immutable original objects with exact length/SHA, original/CT125/CT248 full 695/701 parity including negative cases, release Rust semantic typecheck, actual `C169/C13a/C13b/D/N2_actual` values, same-host A/A and ABBA route/whole-solve costs, matched strongest rho/BSGS/frontier-IC, setup/LA/transfer/recovery/verification/RSS, confidence intervals and signed PCC. The additive selected direct-retained primitive *hypothesis* is `C169-(C13a+C13b)`; norm doubling cancels. No complete single-target ECDLP advantage is established.

## Reproduction (source-only; zero paid compute)

On the PR head checkout:

```sh
b=experiments/chained-transfer-public-target
python3 -S "$b/norm-point-reuse-01/ct248_scoped_sample_audit.py" --self-test
python3 -O -S "$b/norm-point-reuse-01/ct248_scoped_sample_audit.py" --self-test
```

The future native-data command remains `python3 -S "$b/norm-point-reuse-01/ct248_scoped_sample_audit.py" --log <unfiltered-single-test-combined-output>`. This will fail closed until all 144 events, all 48 vectors, **and** the genuine runtime lifetime event exist.

**Sources checked:** original CT248 Rust generator `ct244_primitive_probe.py` and previous record-only auditor; immutable selected `src/tests.rs` blob `bcd27773a7b179c3beeb3d5782a5de97a7df19f2`; cryptanalysis #1871, #1533, #1748; crypto #3877, #4215, #4715, issue #3904. Research-KB service was not accessible through this execution interface and no absence claim is made.
