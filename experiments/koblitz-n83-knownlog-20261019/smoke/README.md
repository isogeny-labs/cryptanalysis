# Local smoke (cloud-agent VM): diagnostics, not timing evidence

Everything here was run on the cloud-agent VM, a shared 4-vCPU Xeon. The
exactness fields (scalars, relations, probe counts, digests, verifier
verdicts) are exact. The times are **local** and are not evidence.

- **Producer.** No rank-probe producer was built locally, because disk was
  tight. The smoke used the rotation-key producer from the scratch
  build of `claude/n83-rotkey` (sha256 `08ead085...`). Its source is the
  rank-probe producer plus additions to the rank stage only (the diff adds
  lines and changes only the rank-solve selector), so its cold path is the
  rank-probe producer's. Check: on B's K600 base it reproduced, through
  `../koblitz-n83-rankprobe-20261019/arm.py` with all of that wrapper's
  gates, B's index digests and the archived Q0 Feistel identity (relation
  [77273, 22971, 54962, 62539], 1,987,852 probes, scalar 3141592653589793).
  The runner builds the rank-probe producer itself.
- **Generator.** `cargo test` passes 4 tests: field identities, the
  group law with phi(G) = [lambda]G, the comb against double-and-add, and
  SHA-256 known answers (`cargo-test-knownlog-local.txt`, rustc 1.97 locally;
  the runner pins 1.99). Its output is deterministic: three runs per K gave
  byte-identical files. The generator's own clock read 208–241 ms at K600
  and 86–104 ms at K220.
- **Independent verifier** (`knownlog_check_local.json`). Both bases PASS
  every check in the pinned oracle: all 600 and 220 logs [a_j]G = R_j, the
  scalars against the declared rule, all 99,600 and 36,520 points as
  ±phi^s(R_j) with labels ±lambda^s, distinct orbits, the base hash, and the
  frozen digests. All three planted corruptions are detected (a log off by
  one, a label coefficient changed, an orbit point replaced).
- **Q0** (`run_schedule.py --segments O1`, `o1_rows_local.json`,
  `o1_correctness_local.json`). All 5 rows are valid, and every correctness
  check that applies to Q0 passes:
  - cP gives the archived identity;
  - cL600 gives relation [25923, 52400, 11104, 19613] with 2,155,400 probes;
  - cL220 and cLaa give [30585, 1963, 20417, 30373] with 801,863 probes;
  - every arm recovers scalar 3141592653589793;
  - cLX: the producer refused the planted table (exit 101, "factor log 1
    does not map G to its representative").

  These identities and the two bases' index digests are frozen in
  `protocol.json` (from `smoke_local.json`). Local cold times on Q0:
  - cL600: 31.1 s end to end (generation 0.22 s, index 27.3 s);
  - cL220: 4.47 s (generation 0.09 s, index 3.39 s, online 0.28 s);
  - cP: 31.4 s.
- **Receipt verifier.** `verifier_synthetic_local.json` runs
  `verify_receipt.py` on a synthetic receipt. It contains the archived run's
  cP, kP and rT rows and this smoke's known-log rows, with fabricated online
  times. The statistics path runs to the end. The scalar, relation and Q0
  gates fail by construction, so the reading is `invalid`, as it should be.
