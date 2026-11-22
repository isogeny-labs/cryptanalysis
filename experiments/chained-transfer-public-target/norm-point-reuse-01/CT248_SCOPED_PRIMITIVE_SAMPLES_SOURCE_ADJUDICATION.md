# CT248 — route-local physical primitive sampling source gate (2026-11-19)

**Standing:** [pcc:unverified]. Source/guard implementation and independently authored audit self-tests have been exercised in GitHub-hosted CI. **No original native sample has yet been collected.** This is not physical pricing, an independently timed replay, a complete single-target solve or a computational advantage.

## Discriminating defect found

CT244's opt-in seven-channel timer was cumulative over one `Runtime`; it emitted only at destruction. The pinned test `fixed-jacobian-chain-evaluator-01/src/tests.rs` (Git blob `bcd27773a7b179c3beeb3d5782a5de97a7df19f2`) resets the *original source call counters* separately before each of **48 × 3 = 144** selected direct/serial/retained arms. Before CT248, no timer reset/snapshot aligned the measurements to those existing arm boundaries. Therefore one CT244 lifetime-clock sum **could not** support a source-matched estimate of direct-versus-retained physical cost; it also included unrelated workload.

## Exact additive remedy in draft PR #1871

- Prospective protocol `CT248_SCOPED_PRIMITIVE_SAMPLES_PROTOCOL.md` committed before implementation as `b00bf141`.
- Generated *separate* priced sibling, not original source or CT125 derivative, has an independent seven-slot epoch timer. Existing CT244 cumulative clock remains available, explicitly unpaired.
- The existing `Runtime::reset_calls()` also clears the epoch clock **only when** `CT244_PRIMITIVE_TRACE=1`; `Runtime::calls()` checks exact C13 (four directions), C169 (two directions), and D (target doubling) epoch counts against the **original same-arm** `Calls` counters, then emits a `CT248_PRIMITIVE_SAMPLE` record with monotonically checked sample sequence. Mismatches panic. When tracing is off, original counters and outputs are unchanged; no map, halving or verification work is added.
- The separately implemented `ct248_scoped_sample_audit.py` requires *exactly* 144 original arm samples plus **one** original 48-vector source record, checks all seven primitive directions in direct/literal/retained sequence, preserves nonzero/zero/exceptional counters, rejects Boolean-as-integer aliasing, missing/duplicate entries and mutated source route counters, and will compute only a per-sample **eval/doubling-expression** delta. It does not assert a full route or ECDLP wall-time delta.

## Hosted evidence (source only)

- [CT248 exact-head source/auditor CI #44641827718](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44641827718) **PASSED**, job `135974521010` at source `7ddb94b4554c071c4df1e97177d8f22a52422a90`. Python normal and `-O` each rejected **11 source mutations** and **17 separately authored auditor mutations**. Separate Rust package generation and `rustfmt` syntax parse passed; the original/evaluator test blobs, seven slots, exact counter parity strings and declared 144 sample expectation passed source guards.
- [CT125 exact-source guard #44641827632](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44641827632) also passed. These checks do **not** constitute a native semantic typecheck or independently signed PCC.
- [CT246 read-only diagnostic #44641827751](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44641827751) **passed as a diagnostic** and still reported `CT247_SESSION_TOKEN_PRESENT=false`, `STS_CLASS=invalid_token`, `HEAD_CLASS=forbidden_403` at the same head. No original six-artifact custody was established.

## Exact cost attribution and mathematical interpretation

The frozen **CT198** 48-packet source-counter audit (cryptanalysis PR #1748) established the *original* direct169-versus-strongest-retained bookkeeping: both routes perform one target norm doubling after CT125 norm reuse. In an additive model the contribution cancels:

`cost(direct) - cost(retained) = C169 - (C13a + C13b)`

for the selected physical map/doubling expressions, **not** `C169 - C13a - C13b - D`. Literal sequential has two norm doublings and four degree-13 evaluations, so it is a weaker comparator. This is a **counter identity**, not an observed positive time delta. Timer overhead, the different input points to each map, admission, nonlinear field arithmetic and setup must be measured rather than equating map degree with actual time.

The precise decision rule after native replay is to compare paired **complete route** wall costs, and finally fully charged single-target ECDLP costs on the same source, against strongest rho/BSGS/frontier IC. A route-local clock advantage alone cannot certify complete-solve improvement.

## Reproducibility and next gating

After an approved credential administrator restores the valid long-term AWS key pair or temporary key/secret/token triplet (privately), require successful read-only STS and **all six** exact SHA+length-verified original model objects via unchanged CT245. Then run Rust 1.99.1 release semantic typecheck and bounded original/CT125/CT248 full 695/701-record tests with all original failures preserved. Do **not** substitute any model fixture, suppress strict parity, or launch paid EKS/Spot without existing admission.

**Source-only offline command sequence** (with an exact checkout of PR #1871):
```sh
b=experiments/chained-transfer-public-target
python3 -S "$b/norm-point-reuse-01/ct244_primitive_probe.py" --original "$b/fixed-jacobian-chain-evaluator-01" --self-test
python3 -O -S "$b/norm-point-reuse-01/ct244_primitive_probe.py" --original "$b/fixed-jacobian-chain-evaluator-01" --self-test
python3 -S "$b/norm-point-reuse-01/ct248_scoped_sample_audit.py" --self-test
python3 -O -S "$b/norm-point-reuse-01/ct248_scoped_sample_audit.py" --self-test
```

If and only if original logged raw native data are later available, run `python3 -S "$b/norm-point-reuse-01/ct248_scoped_sample_audit.py" --log <combined-unfiltered-native-output>`; absence of any of the **144 exact rows** is a failure, not a recoverable filter. The native tests are **not** started by these commands.

**Open scientific gates:** authenticated original 695/701 record integrity; native typecheck and independent full arithmetic replay; actual C169/C13a/C13b/D and `N2_actual`; isolated same-host A/A and ABBA, sufficient rounds and confidence intervals; RSS; cold single-target complete transfer + IC relation/LA/target/verification; matched optimized rho/BSGS/frontier IC; separately signed PCC; protected merge gates. If nonpositive primitive or complete route improvement, record negative and advance a different lead. No speedup claimed.
