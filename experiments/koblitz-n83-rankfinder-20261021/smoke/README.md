# Local correctness smoke of the frozen schedule (not timing evidence)

This smoke ran after `protocol.json` and `schedule.json` were frozen
(protocol sha256 `3209eee1...`, schedule `6810d403...`) and did not change
them. It ran on the cloud-agent VM (shared, 4 vCPU Intel Xeon @ 2.10 GHz)
with `run_schedule.py --segments O1,P1 --cpu 3`. The three binaries came
from one local `cargo build`:

- row `03009c12...` (`ic_online_indexbuild2_r770`);
- rank finder `c38ec700...` (`ic_online_rankfinder_r770`);
- rho `26fc07e9...`.

The toolchain was 1.97; the workflow uses 1.99. `check_log_table.py` ran
first ([`log-table-check.json`](log-table-check.json)): K600, M38 and M10
PASS, and the planted corruptions were rejected.

The 29 rows covered all 6 Q0 arms and the whole P1 segment. That includes
every one of these arms:

- kM38IC, cM38IC (side A, the row);
- kM38RF, cM38RF (side B, the rank finder);
- kM38RFaa, cM38RFaa;
- kM38RFX (planted, frame_plant);
- rT.

All 29 rows were valid ([`runs.jsonl`](runs.jsonl)).
`verify_receipt.py --correctness-only`
([`correctness_smoke.json`](correctness_smoke.json)) found every gate true
except the probe-law band (explained below). The gates that passed:

- one index and layout digest set per base, equal to the frozen one, on
  **K600, M38 and M10**, for both binaries;
- Q0 identities on all 6 arms;
- one scalar, relation and probe count per point, replayed in the oracle;
- rank tables equal to the frozen tables;
- per seed, identical relation digests, probe vectors, root calls and
  counters:
  - seeds 1801, 1802 and 1803 across kM38IC, kM38RF and kM38RFaa;
  - the planted seed 7 across kM38RF and kM38RFX;
- **every IC row's `rank_probe_pipeline` was its arm's**;
- every row ran its arm's binary;
- placement, CPU identity, schedule identity and order;
- the pre-timing table and closure check.

The planted process kM38RFX checked **12,853,712** frame candidates against
the rank-cut lift_scan keys and wrote the frozen table. Every other rank row
checked 0. Every rank row built one frame per attempt (16).

**The probe-law gate was false at smoke size.** It pools kM38IC's probes per
relation over its distinct seeds. Here there are only 3 seeds (48 attempts):
estimate 1.298, bootstrap interval [1.034, 1.597]. The frozen gate uses 36
seeds and 576 attempts. The design-stage simulation from the parent run's
576 attempts gives a 99.9% pass rate at the archived law. kM38IC is the
row's unchanged binary, and every rank row of both binaries had identical
per-attempt probe vectors per seed. So this is a small-sample value, not an
effect of the change. It is recorded here as it fell, and the run decides
it.
