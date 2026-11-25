# Local correctness smoke (cloud-agent VM; not timing evidence)

Run on 2026-10-21 before freezing, with the frozen binaries
(`ic_online_indexbuild2_r770` 61f0b9e2..., `ic_online_onlineframe2_r770`
6517ec27..., `rho_tuned_r770` 7846f921..., rustc 1.97; the workflow pins
1.99) and the design that was then frozen unchanged (the draft protocol had
the same arms, design and schedule; only the power, exactness and local-digest
fields were filled in afterwards):

```
python3 run_schedule.py --bin-dir <bins> --receipt-dir <panel> --cpu 2 --segments O1,P1 --deadline-min 300
python3 verify_receipt.py <panel> --correctness-only
python3 summarize_exactness.py --receipt <panel> --cargo-test cargo-test-online-onlineframe2.txt
```

* `runs.jsonl`: the 32 runner rows (O1: 7 Q0 processes; P1: 25 processes of
  point s000). All valid. The per-row stdout records (raw producer output)
  are summarized in `../inputs/local_exactness.json` and not kept here.
* `correctness_O1_P1.json`: every correctness gate of `verify_receipt.py`
  true, including the new one-root-call-and-relation-check gate.
* `cargo-test-online-onlineframe2.txt`: the derived binary's 35 crate tests.
* `log-table-check.json`: B's table and both closure bases re-verified in the
  pinned oracle, planted corruptions rejected (PASS).

The process times in `runs.jsonl` come from a shared VM and are not
evidence of anything.
