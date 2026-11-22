# Local validation (cloud-agent VM; diagnostics only)

Everything here ran on the cloud-agent VM: a shared 4-vCPU Intel Xeon guest
at 2.1 GHz, with transparent huge pages set to `madvise` (the runner uses
`always`), using rustc 1.97.0 (the runner pins 1.99.0). Some processes ran
concurrently. **None of these times is timing evidence.** They check
correctness and give rough sizes.

## Derivation and tests

- `make_rankprobe_source.py` is byte-identical to the rank-probe
  experiment's `make_online_source.py` (sha256 `804cc965...`, its
  protocol's `online_derivation` pin). Its parents are that experiment's
  verbatim copies. It reproduces the rank-probe producer's frozen digest,
  `d4394df3...`; `make_online_source.py` checks this on every derivation.
- The nine index-lift edits then apply, with every counted replacement
  matching, giving the producer whose digest `protocol.json` pins.
  `restore.py` re-derives it and checks every pin.
- `cargo test --release --locked --bins` (`cargo-test-online.txt`): all 20
  producer tests pass (the rank-probe producer's 18 and two new ones), plus
  the 4 tuned-rho tests; lift2's 24 tests pass (`cargo-test-lift2.txt`). The
  two new tests:
  - `every_index_canonicalizer_builds_the_same_layout`: on a 9-orbit base,
    for the base and the compact table, `lift` and `lift_plant` build the
    same stored-state and table-slot digests, the same B-style digests and
    the same slot array, word for word, as `selected`; `lift_plant` checks
    every insert.
  - `lift_scan_equals_the_selected_canonicalizer_with_its_shift`: on
    400,005 words (0, all-ones, small words, and 400,000 random and sparse
    words) lift_scan returns the selected canonicalizer's key and shift.
- A first draft put the layout digests inside the B-style digest function,
  which the stacked tests compare across layouts (unfolded against folded,
  base against compact); that test failed, as it should, and the layout
  digests moved beside it in the summary. The frozen producer is the second
  draft.

## Every index mode on Q0 (`exactness_local.py cold`, `exactness_cold_local.json`)

Four concurrent processes on Q0 with the verified cached table, one per
index mode, with `arm.py`'s environment:

| process | index canonicalizer | scan self-test | roots checked | stored-state blake3 | table-slot blake3 | B's digests | relation, scalar, probes | index build (diagnostic) | scan self-test (diagnostic) |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: |
| cP | selected | full | 0 | `d8cfe443...` | `5f53764e...` | = B's | = archived Q0 (1,987,852) | 41.5 s | 2.40 s |
| cPI | lift | full | 0 | `d8cfe443...` | `5f53764e...` | = B's | = archived Q0 | 33.4 s | 2.97 s |
| cPIT | lift | sampled | 0 | `d8cfe443...` | `5f53764e...` | = B's | = archived Q0 | 32.9 s | 0.006 s |
| cPIX | lift_plant | full | 29,880,600 | `d8cfe443...` | `5f53764e...` | = B's | = archived Q0 | 43.7 s | 2.35 s |

- **The layout is identical, not only equivalent.** All four index modes
  give the same stored states and the same table slots, byte for byte, and
  B's logical-state and table-map digests. These two layout digests are
  frozen in `protocol.json` (`online.layout_digest`) and gated in every IC
  process of the run.
- cPIX compared every one of the 29,880,600 index roots (2 x 14,940,300
  stored states) with the selected canonicalizer: no difference.

## Full K600 rank stages against the archive (`exactness_local.py rank`, `exactness_rank_local.json`)

The inputs were rank seed 301 and point s000 of the rank-probe panel: the
inputs of run 39214027289's block K1 (archived kP). Two concurrent processes:
kP (selected index) and kPI (lift_scan index), both `KIC_RANK_SOLVE=frame`.

| arm | rank, attempts | relation digest | per-attempt probes | root calls | counters | factor-log table | target relation, scalar, probes | layout digests | index build (diagnostic) | rank stage (diagnostic) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| kP | 600, 600 | = archive | = archive (600 of 600; 982,994,775) | = archive (491,547,414) | = archive | = B's | = archive | = frozen | 30.4 s | 223.3 s |
| kPI | 600, 600 | = archive | = archive | = archive | = archive | = B's | = archive | = frozen | 18.0 s | 222.5 s |

- Counters in both: 600 resolved hits, 308 swapped pairs, 0 fallback
  states, 0 exceptional inputs, 600 frames, 0 planted checks, the same as
  the archived kP row.
- The rank stage on the lift_scan-built index took what it took on the
  baseline index (kPI / kP 0.996 on this VM, concurrent): the premise of
  the shared rank stage. Diagnostic only; the sharing control checks it on
  the runner.

## Runner, wrapper and verifier (`run_schedule.py`, `correctness_O1_C1_K1.json`)

`run_schedule.py --segments O1,C1,K1` ran 12 rows of the provisional
schedule through `arm.py` on one pinned CPU, sequentially: O1 (cP, cPI,
cPIT, cPIX on Q0), C1 (all six cold arms on point s000 of the new panel)
and K1 (kP and kPI, the new rank seed 401). Every row is valid (every
`arm.py` check, including B's digests, the frozen layout digests, the index
canonicalizer, the planted check count and the scan self-test mode), and
`verify_receipt.py --correctness-only` passes every check: Q0 equal to the
archived Feistel identity in all four Q0 arms; one relation, probe count and
scalar on s000 across cP, cPaa, cPI, cPIT, cPIX, kP, kPI and rT (oracle
replay); one index digest set across every IC process; and in K1 one
relation digest, probe vector, root-call total and counter set across kP
and kPI, with B's table in both. The protocol and schedule were then
regenerated, unchanged in design, with the final frozen time.

## Verifier statistics on synthetic rows (`synthetic_stats.py`)

Run 39214027289's archived rows, renamed (cR to cP, cP to cPaa, kP to kP,
kPaa to kPI; no timing of this experiment):

- `synthetic_archived.json`: cPI is the archived cPI (lift_scan), so the
  expected primary is the archived (K + cP) / (K + cPI). R = 1.0354
  [1.0337, 1.0372], "improvement"; the per-arm form 1.0351 [1.0337,
  1.0365]; sharing kPI / kP 1.0004; controls pass.
- `synthetic_null.json`: cPI is a copy of the archived cP (the same cold
  code as the renamed cP): R = 1.0000 [0.9998, 1.0002], "not separated";
  controls pass.
