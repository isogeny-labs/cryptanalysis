# Local diagnostics (cloud-agent VM; not timing evidence)

The cloud-agent VM is a shared 4-vCPU Xeon. Everything here checks
correctness. None of it is timing evidence.

- **Decisive test.** `../inputs/local_decisive_test.json` is a frozen input,
  read by `make_protocol.py`. It records, for each closure base:
  - the independent verification of the base and its table, with the
    planted corruptions;
  - every local rank block: seeds 301–305 for M10 and 301–309 for M38;
  - the probe law;
  - the index digests and the Q0 identity.

  The README's "Local decisive test" section summarises it.
- **Producer tests.** `cargo-test-online.txt` is `cargo test --release
  --bins` on the derived producer: 19 producer tests, including the new
  `closure_multiplier_is_its_label`, and the 4 tuned-rho tests. All pass.
- **Runner smoke.** `correctness_smoke.json` is `run_schedule.py` on
  segments O1, C1, K3 and K1 (`--segments`). It covers:
  - Q0 on cP, cM38 and cM10;
  - point s000 on every cold arm and rT;
  - every rank arm, including the baseline kP with 600 attempts, the
    planted kM38X, and kM10.

  It also includes `verify_receipt.py --correctness-only` on those rows and
  the pre-timing `check_log_table.py` result. The probe-law gate is
  evaluated on the rows present. It reads false on a single 16-attempt
  block, as expected: the band is sized for 256 attempts.
- **Verifier statistics.** `synthetic_stats.json` comes from
  `synthetic_stats.py`, which runs the frozen statistics and decision rule
  on synthetic rows built from the smoke rows, in three scenarios:
  - as measured;
  - no end-to-end effect;
  - a broken A/A.
