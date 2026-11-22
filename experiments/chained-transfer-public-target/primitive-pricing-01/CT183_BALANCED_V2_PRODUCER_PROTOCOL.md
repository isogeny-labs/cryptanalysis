# CT183 — Prospective counterbalanced v2 cold-process producer

2026-11-17 UTC · [pcc:unverified] · draft [cryptanalysis #1713](https://github.com/isogeny-labs/cryptanalysis/pull/1713), stacked on the bounded CT178 source [#1706](https://github.com/isogeny-labs/cryptanalysis/pull/1706). Distinct CT182 offline reader remains in draft [#1711](https://github.com/isogeny-labs/cryptanalysis/pull/1711). Frozen **before** implementing the CT183 producer.

## Exact source and wire contract

Keep the original CT125 arithmetic and 48 public packets, pinned Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`, 19-word target, 21 native counters, child schema `ct175-single-public-packet-cold-route/v1` and strict CT176 native checks unaltered. Do not edit CT176/v1 evidence. New producer is a separate executable Python entry point reusing CT178's bounded POSIX process execution, raw stdout/stderr capture, per-child timeout, monotonic aggregate deadline, host/affinity guard and fail-closed terminal status.

Match CT182's offline reader byte-for-byte:
- Manifest schema `ct182-counterbalanced-cold-public-process-panel/v2`
- Schedule identity `ct181-block-packet-parity-ABBA-BAAB/v2`
- Eight blocks; shuffle packet IDs by `random.Random(20261117 + block).shuffle(list(range(48)))`.
- For each packet, ABBA plus A/A when `(block + index) % 2 == 0`; otherwise BAAB plus A/A. `A=direct_composite`, `B=strongest_retained_lift_chain`. Six ordered process positions per packet-block, 2,304 slots total; each packet has four blocks in each treatment order.
- Hash of ASCII `json.dumps(list(roster), separators=(",", ":"), ensure_ascii=True)`: `1dddb4839321ad6560fd429330778aa083ff3a13625393250e964c05f9fc5ee4` (independently calculated from the published ordering); record as `order_roster_sha256`.
- Manifest includes original fixture Git blob, SHA-256, blocks, seed, packets, processes, order schema, roster digest, binary path and SHA-256, timeout and strictly positive explicit aggregate budget, host metadata; samples retain original CT176 JSON fields and exact order/arm/argv. Terminal is valid only after all 2,304 attempts are successful and the aggregate deadline was not exceeded.
- Default is **plan-only**, with no binary execution. Actual execution requires `--execute --admission-approved` plus original owner/provider approval and original authorized EKS/budget conditions; flags are not themselves permission. Fail before opening output on missing admission, missing executable digest, non-executable binary, invalid budget, fixture mismatch, malformed schema.
- Preserve all failed or truncated subprocess evidence as an incomplete panel, never reclassify it as complete. Exclusive output creation; no replacement of original raw evidence.

## Validation and limitations

Run Python normal and `-O` source tests and plan-only against the authentic immutable 48-packet fixture; exercise full deterministic order/hash and v1 isolation, invalid budgets, non-native fake failure/timeout, terminal refusal. CI should compare normal and optimized plan outputs after removing dynamic host metadata if necessary. A separate exact-head reader test after reconciling the two draft stacks must accept a **complete synthetic** v2 producer panel and reject v1/mutations. No synthetic ratio is a measured advantage.

The acceptance gate remains original independent 695/701 custody; native typecheck and 48 arithmetic parity; authorized paired cold same-host `C169`, `C13a`, `C13b`, `N2_actual`, `D_padd` pricing; actual complete cold single-target solve versus strongest rho/BSGS/IC including setup, transfer, inversion, LA, recovery and memory; uncertainty and signed independent PCC. No native benchmark is authorized by this protocol. No paid work, cross-characteristic speedup, or complete ECDLP cost advantage is claimed. [pcc:unverified]
