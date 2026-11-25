# CT178 — bounded aggregate duration for the 48-packet cold transfer panel

Date: 2026-11-17. Source/producer-only standing: **[pcc:unverified]**.

## Finding and exact scope
The previously merged CT176 collector and open CT177 repair enforced **120 s
per child**, but not an aggregate limit for 48 packets x 8 blocks x 6 arms =
2,304 fresh processes. The sum of per-process timeouts could reach
276,480 s = 76.8 h before overhead (analytical upper bound, **not a run**).
Even an admitted host must not silently spend this much time on a frozen panel.

The CT178 implementation requires an **explicit positive**
`--panel-wall-seconds N` in *execution mode only*. `--execute` still
requires `--admission-approved`, pinned native binary digest, original
fixture and genuine external owner/provider budget approval. No default
aggregate time is silently chosen. Plan-only mode remains unchanged.

The monotonic panel deadline begins before manifest creation. For each
subprocess, the remaining aggregate allowance is intersected with the
per-child timeout, then the existing bounded reader and process-group
termination enforce the resulting child timeout. Before each next launch
the deadline is checked. Expiry during/after a sample produces an
**incomplete terminal refusal**, even if the individual output was valid.
No observations are silently discarded; incomplete output stays as raw
JSONL under exclusive creation. Original public points, counters, route
labels and arithmetic were not changed.

## Source-based tests
Three new synthetic tests cover explicit positive type-strict budget,
remaining time intersection and expiry without spawn, and terminal refusal
despite a mathematically valid last sample. The existing 29 tests check the
actual frozen 48-packet roster and mock validation/capture failure modes.
The exact-head scoped CI job must be read before a pass is claimed.
There is **no native Rust typecheck, execution or timing** in this change.

## Source identities
- Root coordination: crypto [#3877](https://github.com/isogeny-labs/crypto/pull/3877), live [#3904](https://github.com/isogeny-labs/crypto/issues/3904).
- Baseline: cryptanalysis [#1700](https://github.com/isogeny-labs/cryptanalysis/pull/1700) merged and [#1706](https://github.com/isogeny-labs/cryptanalysis/pull/1706) open.
- Immutable prospective protocol: `CT178_PANEL_DEADLINE_PROTOCOL.md`, committed before code at `c3574272b2eb9e0267cc5acb0c005a8e62a6a9d1`.
- Implementation commit: `d873cfcf115317427caf870e6b8c0dc7ceca1a64`; three tests: `e6f4701c6afd873d318439cd29b609e341e6ebed`.
- Source inspections: cryptanalysis `AGENTS.md`, current CT175/176/177 collector, test and newest session log, active queue and concurrent crypto Richelot PR #4514. KB service not exposed in this runtime; repo source fallback only.

## Reproduction
```sh
python3 -m unittest discover -s experiments/chained-transfer-public-target/primitive-pricing-01 -p test_ct176_cold_process_collector.py -v
python3 -O -m unittest discover -s experiments/chained-transfer-public-target/primitive-pricing-01 -p test_ct176_cold_process_collector.py -v
# Safe plan; N and native binary intentionally omitted:
python3 experiments/chained-transfer-public-target/primitive-pricing-01/ct176_cold_process_collector.py --fixture <frozen-CT125-48-json>
# Native execution intentionally NOT performed; requires external authorization:
# ... --execute --admission-approved --panel-wall-seconds N --timeout-seconds 120
```

## Remaining scientific objective
Independent 695/701-object custody and full 48-case native parity, actual
same-host C169/C13a/C13b/N2_actual/D prices, then complete prime-field
public-target rho/BSGS/IC/transfer timing with setup and peak RSS, uncertainty,
and independently signed PCC. A fresh-process *transfer-only* panel is not
an end-to-end discrete-log solve. No compute was launched, and no advantage is claimed.

## Errors / caveats
An aggregate budget is a safety guard, not a benchmarking result. A process
may consume a small amount of setup/cleanup time after the deadline:
the **terminal** classification will still refuse the panel. Any published
timing analysis must retain failure/censoring and not treat truncated panels
as paired complete observations. [pcc:unverified]
