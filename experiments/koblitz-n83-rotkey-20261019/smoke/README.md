# Local diagnostics (cloud-agent VM) for koblitz-n83-rotkey-20261019

Everything here is a **local diagnostic**: a shared 4-vCPU Xeon VM at 2.1 GHz
(transparent huge pages `madvise`; the GitHub runner uses `always`), with
other agents' builds and runs on the same machine (load average 4 to 10
during these runs). Exactness results are exact; times are not timing
evidence and never enter the frozen rule.

| File | What it is |
| --- | --- |
| `rotkey_micro.rs` | standalone microbenchmark: rotkey(v) = v^83 in F2[X]/(X^83+1) by carry-less multiplication, checked against a reference product and under rotation, against lift_scan on 4,096 independent random words (batch throughput) and as a dependent chain (latency); `build` mode times re-keying a 2^26-slot table of 29,878,182 random keys |
| `key_micro_local.json` | its output |
| `rank_exactness_local.json` | three concurrent full K600 rank stages (`frame`, `rotkey`, `rotkey_plant`) on the inputs of run 39214027289's block K1 (rank seed 301, point s000 of rankprobe-cold-v1), compared with the archived kP row |
| `rank_pair_local.json` | a second pair (`rotkey`, `frame`) on the same inputs, two concurrent processes on swapped CPUs |
| `cargo-test-online.txt`, `cargo-test-lift2.txt` | the crate tests (21 producer tests including the 3 new ones, 4 tuned-rho tests, 24 lift2 tests) |
| `design_inputs.json` | the numbers the protocol records as design inputs, copied from the files above |
| `correctness_O1_C1_K1_two_rows.json` | `run_schedule.py --segments O1,C1,K1 --max-runs-per-segment 2` on the frozen protocol and schedule, then `verify_receipt.py --correctness-only`. O1 ran cP and cK on Q0, C1 ran two of cP, cK and rT on s000, and K1 ran kK and kKaa (rank seed 501). All 6 rows are valid and every check passes: Q0 equals the archived Feistel identity, one scalar per point with the oracle replay, B's factor-log table, the rank identity, 0 collisions and 600 verified hits in both rank rows |
