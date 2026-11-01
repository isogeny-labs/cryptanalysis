# Local correctness smoke of the frozen schedule (not timing evidence)

This smoke ran after `protocol.json` and `schedule.json` were frozen
(protocol sha256 `5cee1a72...`, schedule `f5ac4c17...`) and did not change
them. It used the cloud-agent VM (shared, 4 vCPU Intel Xeon @ 2.10 GHz) and
`run_schedule.py --segments O1,P1 --cpu 2`, with the three binaries from one
local `cargo build`:

- row `5db73e65...` (`ic_online_indexbuild_r770`);
- round 2 `6b0ec06b...` (`ic_online_indexbuild2_r770`);
- rho `8e602007...`.

The toolchain was 1.97; the workflow uses 1.99. `check_log_table.py` ran
first ([`log-table-check.json`](log-table-check.json): K600, M38 and M10
PASS, planted corruptions rejected).

The 29 rows covered all 6 Q0 arms and the whole P1 segment, every one of
these arms:

- kM38IB, cM38IB (side A, the row);
- kM38IC, cM38IC (side B, round 2);
- kM38ICaa, cM38ICaa;
- cM38ICX;
- rT.

All 29 rows were valid. `verify_receipt.py --correctness-only`
([`correctness_smoke.json`](correctness_smoke.json)) found **every gate
true**:

- one index and layout digest set per base, equal to the frozen one, on
  **K600, M38 and M10** (both binaries);
- Q0 identities on all 6 arms;
- one scalar, relation and probe count per point, replayed in the oracle;
- rank tables equal to the frozen tables;
- per seed (1501, 1502, 1503), identical relation digests, probe vectors,
  root calls and counters across kM38IB, kM38IC and kM38ICaa;
- every row ran its arm's binary;
- placement, CPU identity, schedule identity and order;
- the pre-timing table and closure check.

The `runner_identity` gate passes because `--correctness-only` allows the
smoke subset.

The planted row cM38ICX checked 30,682,720 roots and kept the frozen layout.
`runs.jsonl` is the runner's ledger. The local times in it are diagnostics on
a contended VM, not evidence. For example, the M38 index build in the cold
processes was 9.58 to 10.45 s on the row (4 processes) against 7.63 to
9.31 s on round 2 (9 processes, including the A/A copies). That is a
smaller gap than the three alternating pairs that set the modelled factor
(0.729). At this smoke's ratio of means (about 0.87) the model would predict about
1.07 end to end, and the frozen design's power is still 1.00 at 1.05.
