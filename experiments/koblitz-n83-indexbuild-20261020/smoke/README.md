# Local correctness smoke of the frozen schedule (not timing evidence)

This smoke ran after `protocol.json` and `schedule.json` were frozen
(protocol sha256 `3073d0c5...`, schedule `5b1db827...`) and did not change
them. It used the cloud-agent VM (shared, 4 vCPU Intel Xeon @ 2.10 GHz, KVM)
and `run_schedule.py --segments O1,P1 --cpu 2`, with the three binaries from
one local `cargo build`:

- row `491e1951...`;
- derived `c73eab37...`;
- rho `0018f6dc...`.

The toolchain was 1.97; the workflow uses 1.99.

The 29 rows covered all 6 Q0 arms and the whole P1 segment, every one of
these arms:

- kM38I, cM38I;
- kM38IB, cM38IB;
- kM38IBaa, cM38IBaa;
- cM38IBX;
- rT.

All 29 rows were valid. `verify_receipt.py --correctness-only`
([`correctness_smoke.json`](correctness_smoke.json)) found every gate true
except `pre_timing_tables_and_closure_bases_verified`. That gate is unknown
here because `check_log_table.py` runs in the workflow only:

- one index and layout digest set per base, equal to the frozen one, on
  **K600, M38 and M10** (both binaries);
- Q0 identities on all 6 arms;
- one scalar, relation and probe count per point, replayed in the oracle;
- rank tables equal to the frozen tables;
- per seed (1401, 1402, 1403), identical relation digests, probe vectors,
  root calls and counters across kM38I, kM38IB and kM38IBaa;
- every row ran its arm's binary;
- placement, CPU identity, schedule identity and order.

The `runner_identity` gate passes because `--correctness-only` allows the
smoke subset.

The planted row cM38IBX checked 30,682,720 roots and kept the frozen layout.
`runs.jsonl` is the runner's ledger. The local times in it (for example, the
M38 index build at about 20 s on the row against about 10.5 s on the derived
producer) are diagnostics on a contended VM, not evidence.
