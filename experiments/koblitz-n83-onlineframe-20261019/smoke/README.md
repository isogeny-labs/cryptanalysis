# Local diagnostics (cloud-agent VM): not timing evidence

These were all run on the cloud-agent VM: a shared 4-vCPU machine, with
load about 11 from other builds. The toolchain was rustc 1.97.0, where the
workflow pins 1.99.0. The frozen Tier 1 run decides; nothing here does.

| File | What it is |
| --- | --- |
| `cargo-test-online.txt` | `cargo test --release --locked --bins` of `online/` on the frozen source (`e6a944e6...`): 20 producer tests pass, 2 of them new (`onlineframe_tests`), and 4 tuned-rho tests pass. Paths are redacted. |
| `correctness_first_smoke_with_K1.json` | `run_schedule.py --segments O1,C1,C2,C3,C4,K1` with a first build. Its only difference from the frozen source: the planted arm did not charge the redone S3 work to the online phases, so every cFX row failed the five-phase sum check (exactness was intact). That is the reason for the one-line fix in `make_online_source.py`. The rows that pass the gates include K1 (kP: full rank, B's table, 600 frames, 600 resolved hits, 303 swapped). |
| `correctness_O1_C1-C6.json` | `run_schedule.py --segments O1,C1,...,C6` with the frozen binary: all 34 rows valid, and every correctness check true. |
| `local_diagnostics.json`, `summarize_local.py` | per-row probes, root calls, relation checks, relation, scalar, online ms and online counters from both smokes, plus the local online ratio cS / cF |

## Readings

- **Exactness.** On Q0 and s000–s005, every IC arm (cS, cF, cFaa, cFX)
  gives one scalar, which equals rT's and replays in the oracle. Every IC
  arm also gives:
  - one relation, with the same x codes and intermediates;
  - one probe count;
  - one root-call count and one relation-check count.

  Q0 gives 1,987,852 probes in cS, cF and cFX.
- **Planted control.** cFX compared 6,759,354 candidates on 40,719 states
  with the S3 loop and found no difference. The pair order is all or
  nothing per target:
  - s000, s001 and s003: every pair is swapped (4,169,754 pairs);
  - Q0, s002, s004 and s005: no pair is swapped.

  So both paths of the hit resolution ran.
- **Local timing (diagnostic).** Online cS / cF has a ratio of means of
  1.48 over s000–s005 (per point 0.67–2.11). Locally cFX / cF = 2.42 and
  cF / cFaa = 0.956. The VM's noise exceeds the A/A band, so these numbers
  only show the direction.
