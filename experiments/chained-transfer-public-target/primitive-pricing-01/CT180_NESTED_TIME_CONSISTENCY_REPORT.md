# CT180 — fail-closed nested cold-time evidence audit

2026-11-17 UTC · **[pcc:unverified]** · source and synthetic controls, no actual native timings.

## Concrete defect and correction

CT179 accepted correctly hashed child evidence even when the asserted external subprocess-wall duration was less than the duration of its *own* complete Rust in-process execution. It also accepted child setup+route sums greater than the claimed total. Both inconsistencies can directly change the ABBA direct/retained cost statistic without modifying the unchanged frozen 19-word inputs/outputs or 21 native counters.

The source control follows literal clocks, not a symbolic cost model. CT175 `ct172-replay/src/main.rs` uses Rust `Instant` for setup, selected transfer and total elapsed in one fresh process. CT176 `ct176_cold_process_collector.py` surrounds process creation/exit with Python `perf_counter_ns`. CT180 requires `0 <= setup_ns, 0 < route_ns, 0 < total_ns <= external_ns`, and `setup_ns+route_ns <= total_ns`. The initial CT179 version required positive external time only, and accepted zero native times.

Strict inequality is valid for the nominal Linux monotonic-clock execution contract; if a future target environment cannot provide comparable elapsed durations, evidence must be refused until a separately frozen clock-calibration policy exists. These checks alone cannot prevent coordinated fabricated, internally consistent transcripts, so external attestation and signed PCC are still necessary.

## Reproduction / controls

```sh
root=experiments/chained-transfer-public-target/primitive-pricing-01
python3 -S -m unittest discover -s "$root" -p 'test_ct179_panel_adjudicator.py' -v
python3 -O -S -m unittest discover -s "$root" -p 'test_ct179_panel_adjudicator.py' -v
```

The new synthetic test changes only elapsed durations and recomputes complete stdout SHA/base64 evidence. It tests external=1ns vs native total=330ns; internal total=200ns vs setup110ns+route120ns; native route=340ns vs total330ns; zero route/total; and valid exact boundary total=external=230ns. Existing 2304-row full synthetic panel is preserved. No literal 1.5× ratio from test inputs is scientific evidence.

## Integration / outstanding

CT180 is stacked as [cryptanalysis PR #1710](https://github.com/isogeny-labs/cryptanalysis/pull/1710) against active [CT179 PR #1708](https://github.com/isogeny-labs/cryptanalysis/pull/1708), without touching the parent, frozen vectors, arithmetic evaluator, trust gates or CI scripts. Exact-head CI and review are required before merge; this report does not claim that CI passed.

Still missing: admitted native Rust typecheck, all 48 public Jacobian arithmetic replay, independently authenticated original 695/701 corpus, actual C169/C13a/C13b/N2_actual/D pricing, matched complete single-target prime-field rho/BSGS/IC/transferred solves with setup, LA, correction, verification and memory, and a signed independent PCC verdict. Owner's paid-compute STOP remains in force. [pcc:unverified]

Sources checked: merged [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), current [queue #3904](https://github.com/isogeny-labs/crypto/issues/3904), merged [#4215](https://github.com/isogeny-labs/crypto/pull/4215), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [#1700](https://github.com/isogeny-labs/cryptanalysis/pull/1700), [#1706](https://github.com/isogeny-labs/cryptanalysis/pull/1706), [#1708](https://github.com/isogeny-labs/cryptanalysis/pull/1708), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178); current CT175/CT176/CT179 source and AGENTS.md. Research KB service unexposed; local Rust/Cargo unavailable. No novelty inference.
