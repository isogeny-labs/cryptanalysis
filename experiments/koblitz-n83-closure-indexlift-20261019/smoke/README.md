# Local validation (cloud-agent VM; diagnostics only)

Everything here ran on the cloud-agent VM: a shared 4-vCPU Intel Xeon guest
at 2.1 GHz, with transparent huge pages set to `madvise` (the runner uses
`always`), using rustc 1.97.0 (the runner pins 1.99.0). **None of these
times is timing evidence.** They check correctness.

## Derivation and tests

- `make_online_source.py` re-derives three texts, checks each against its
  frozen digest, and then composes them:
  - the rank-probe producer, `d4394df3...`;
  - the index-lift producer, `7df72603...`, through
    `make_indexlift_source.py`, a verbatim copy of main's
    `koblitz-n83-indexlift-20261019/make_online_source.py`;
  - the closure producer, `8916e034...`, through `make_closure_source.py`, a
    verbatim copy of `koblitz-n83-closure-20261019/make_online_source.py` at
    commit 3761fd260.

  It also checks that the two edit sets commute up to the header comments.
  `restore.py` re-derives the producer and checks every pin
  (`1d328b2e...`).
- `cargo test --release --locked --bins` (`cargo-test-online.txt`): 21
  producer tests pass, including the closure's
  `closure_multiplier_is_its_label` and index-lift's
  `every_index_canonicalizer_builds_the_same_layout` and
  `lift_scan_equals_the_selected_canonicalizer_with_its_shift`. The 4
  tuned-rho tests also pass. The `lift2` crate is the parents' verbatim copy,
  and the workflow tests it.
- `python3 -m unittest test_verify_receipt`: 11 tests pass. They check that
  an unknown gate makes the result invalid, as do a failed layout gate, a
  failed planted exactness check, A/A out of band and an undetected plant.
  They also check that a raw-record digest mismatch, a schedule-identity
  mismatch and invalid base64 are rejected.

## Exactness

- `exactness_local.py cold` → `../inputs/local_layout_test.json`: Q0 on K600,
  M38 and M10, with `KIC_INDEX_CANON` = `selected` and `lift`. Each base has
  one layout pair across the two canonicalizers. K600's pair is index-lift's
  frozen pair. The logical-state and map digests, root entries and Q0
  identities equal the parents' frozen values.
- `exactness_local.py rank` → `exactness_rank_local.json`: two archived
  Tier 1 rank processes were reproduced with `lift`, field for field: kPI of
  run 39290913632 (block K1) and kM38 of run 39305259093 (block K1).

## Runner smoke (`correctness_smoke.json`)

`check_log_table.py` passes for K600, M38 and M10, and the planted
corruptions are caught. `run_schedule.py` ran segments O1, C1 and K1 of the
frozen schedule: 13 rows, all valid, covering every arm. Then
`verify_receipt.py --correctness-only` ran. Every correctness check passes
except the probe-law band, which is false on this **one** block. kM38I's 16
attempts read 1.566 of the law. The frozen gate pools all 16 blocks (256
attempts). In the closure's local test, per-block ratios ranged from 0.58 to
1.35, and the closure run pooled 0.963. On the same block, kPI read 0.920
(600 attempts) and kM10I 1.140 (60 attempts).

This smoke ran the frozen block K1 (seed 1101). Its relations and probe
counts are deterministic, so the Tier 1 run will reproduce them. They are
not timing, and nothing in the protocol was changed after seeing them (the
protocol was frozen before the smoke).
