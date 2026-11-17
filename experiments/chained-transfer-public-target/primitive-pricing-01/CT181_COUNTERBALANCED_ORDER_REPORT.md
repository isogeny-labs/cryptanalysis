# CT181 — position-confounding negative control and balanced design

2026-11-17 UTC · [pcc:unverified] · **source/synthetic test only** · [draft PR #1711](https://github.com/isogeny-labs/cryptanalysis/pull/1711)

## Actual new result

CT179's existing `test_ct179_panel_adjudicator.py:sample` sets 2,000,000 ns in positions 1 and 2, 3,000,000 ns everywhere else, **regardless of whether the arm is degree-169 direct or retained degree-13/13**. Its fixed A/B/B/A/A/A design consequently reports a nominal 1.5 direct/retained timing ratio from **zero intrinsic algorithm difference**, A/A drift zero, and even a degenerate packet-bootstrap generic-stratum CI at 1.5. This directly falsifies the sufficiency of the current positional A/A control for separating arbitrary slot effects from treatment speed.

The counterexample is not a native measurement. In an additive or multiplicative slot-sensitive host, this schedule can manufacture a statistically convincing *transfer-only* gain without any genuine arm difference. Every original public mathematical output and all 21 counters could still be correct. An independently reproduced complete ECDLP advantage has not been demonstrated.

## Source implementation and exact results

Froze [prospective design](CT181_COUNTERBALANCED_ORDER_PROTOCOL.md) at `163ca7f4` before code; [standalone synthetic design](ct181_order_design.py) `4e9d9bf9`, [six negative/positive tests](test_ct181_order_design.py) `c98e4752`, and [normal/-O source CI](../../../..//.github/workflows/ct172-native48-source.yml) `c21a2c71`. The new v2 order is A/B/B/A/A/A in exactly four of eight blocks per packet and B/A/A/B/A/A in the other four, balanced 24/24 within each block, using packet parity plus block parity. It retains exactly 2,304 expected process slots and two A/A controls per packet-block.

Exact-head hosted [source CI #44068535791](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44068535791) passed **6/6** CT181 tests in both normal and optimized Python. Existing CT179 **11/11** and CT176 **24/24** per mode also passed in that job. The same job emitted this synthetic negative/positive pair:

| Controlled input (no measured hardware) | Fixed ABBA direct/retained | Balanced ABBA/BAAB |
|---|---:|---:|
| Identical intrinsic A and B | 1.500 | 1.000 |
| Intrinsic A/B = 1.25, stationary separable slot multipliers | 1.875 | 1.250 |

The 1.500 **is a falsification**, not a positive benchmark. The 1.250 **is a programmed synthetic control**, not an ECDLP result.

## What cannot be inferred

Counterbalance cancels the precise *stationary separable* position multiplier in the design. It does not guarantee removal of evolving block-dependent thermal/load effects, cache state, arm-by-position interaction, treatment carryover, or hostile evidence fabrication. A/A drift must still be recorded, randomized/paired same-host controls retained, and complete raw output independently adjudicated. Only one elliptic/Jacobian source fixture population is represented, not a random sample of curves.

The production CT176/178 collector and CT179/180 adjudicator still use **v1** and are on separate open PR stacks (#1706 versus #1708/#1710). CT181 deliberately leaves those protected sources, the original 48-row fixture and any prior panel unchanged. Before measuring, adopt a **distinct v2 schema** consistently in producer and adjudicator, freeze v2 manifest/roster/estimator, fail closed on v1/v2 cross-reads and maintain full source/hash/benchmark receipts. The original Rust CT175 executable is still not native-typed/executed here; original authenticated 695/701 custody, owner-admitted C169/C13a/C13b/N2_actual/D and complete cold rho/BSGS/IC/transfer comparison, memory, CI, signed PCC remain unresolved. Do not launch paid EKS/Spot/GPU or bypass PR gates.

Sources: source files and previous CT179/180 protocols under this directory; [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [queue #3904](https://github.com/isogeny-labs/crypto/issues/3904), [selected cost #4215](https://github.com/isogeny-labs/crypto/pull/4215), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178). General repeated-run uncertainty methodology: Kalibera and Jones, [*Rigorous Benchmarking in Reasonable Time* (2013)](https://doi.org/10.1145/2464157.2464160). KB MCP not available this session; no novelty claim.
