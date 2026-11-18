# CT197 — strict CT196 native diagnostic reader (source/synthetic report)

Date: 2026-11-17 (America/Denver). **Scientific standing: [pcc:unverified]**. Draft PR [#1745](https://github.com/isogeny-labs/cryptanalysis/pull/1745), based on CT196 [#1743](https://github.com/isogeny-labs/cryptanalysis/pull/1743). The [prospective protocol](CT197_EVIDENCE_PROTOCOL.md) was committed at `a8714452251d73ee8d4b8e2c9962c6db26018368` before implementation.

## Concrete progress

Implemented [ct197_native_evidence.py](ct197_native_evidence.py), a strict **offline** reader for the two-panel CT196 native diagnostic schema. It does not launch any Rust executable and cannot create an authenticated measurement. A production run checks the original public-48 fixture with the existing exact Git-blob guard before processing input. It checks each packet against BOTH transfer routes and validates all 96 expected true target operands, 64 original-panel slots and 64 extra control-panel slots per operand, including the fixed physical ABBA/BAAB treatment assignments, the four warmup blocks, valid decimal timings, exact counter deltas and nested elapsed-time containment.

Specifically, the reader demands exactly 4,608 recorded original slots, 4,608 recorded extra control slots, +2,048 `transported_norm_doubling` calls **per panel per operand**, and the declared total 393,216. It rejects any producer JSON asserting a completed ECDLP solve, forged verified standing or a non-original Git source/fixture blob. It treats peak RSS as an optional **producer assertion**, not independently authenticated memory accounting.

The diagnostic scorer computes one geometric mean of 12 measured within-block physical-operation ratios per packet/route/panel. It then reports a median over the **five generic** packets in each direction×sector×route×panel stratum, with the **single identity packet** reported separately. This yields 64 separate strata (2 directions × 4 sectors × 2 routes × 2 identity statuses × 2 panels), without miscounting the 12 blocks or two routes as independent ECDLP targets. No source-level diagnostic, including a ratio >1, is eligible as a complete-solving result. The first panel is `N2_actual / D_padd`; the independent control panel is `N2_actual / N2_arith_no_counter`.

## Source-only validation and failures

A fully synthetic 48-packet/96-operand construction with 64×2 slots per operand passed the reader, retaining the known **programmed** 1.10 primitive timing ratio in both independent panels. This value is a unit-test oracle, **not observed native performance**. Mutation tests rejected duplicate JSON keys, nonfinite fields, missing/duplicate operands, route/cohort corruption, false PCC/complete-solve standing, erroneous norm counters, invalid/zero/float timing, wrong ABBA slot assignments, warmup leakage, wrong repetition counts, lost optional RSS field and impossible nested process time.

Local commands, run in the directory of these two new Python files:

```sh
python3 -m unittest -q test_ct197_native_evidence.py
python3 -O -m unittest -q test_ct197_native_evidence.py
```

Both succeeded: **5/5 normal, 5/5 optimized Python tests**, each with many mutation subcases. The existing CT192 source-only workflow has been amended to execute both tests without starting native code. Exact-head hosted CI and independent PCC remain **separate** and must be read from the applicable current GitHub Actions runs; a local unit test is not an independent producer verification.

To read a future real retained native JSON artifact after external admission and custody, from the original study directory:

```sh
python3 -S ct197_native_evidence.py --input /absolute/path/ct196-raw.json --output /absolute/path/ct197-diagnostic.json
```

The CLI requires the exact original 48-row checked fixture and labels its output `ct197-unverified-native-diagnostic-reader/v1`. It never produces an authenticated execution certificate. Source reviews used CT125 original, CT192–196 source and protocol, crypto #3877/#4215, cryptanalysis #1523, and the prior CT190 block-effect correction. No novelty or speedup claim is made. Shared research-KB and native Cargo/Rust compilation remained unavailable in the tool runtime.

## Next decisive gate

**No actual measurements were executed.** An independently authenticated original 695/701-record corpus, native all-48 Rust parity and current owner/provider compute admission are needed before this reader can be used to interpret real data. A portable native executable with inspected release assembly and executable hash; paired same-host measurements of C169, C13a, C13b, N2_actual and D; A/A shams and randomized physical route crossover; and complete **cold** prime-field ECDLP cost comparisons versus strongest optimized rho, BSGS and index calculus with setup, transfer, linear algebra, recovery, verification and peak RSS counted are still outstanding. Separate PCC-signed independent reproduction is required for any complete advantage claim.

No paid EKS/Spot/GPU work, protected merge, original source mutation or authorization override occurred. This PR stays draft until all native/custody/PCC/review gates are satisfied. [pcc:unverified]
