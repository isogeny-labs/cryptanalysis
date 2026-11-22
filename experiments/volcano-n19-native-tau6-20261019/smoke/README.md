# Local diagnostics (cloud-agent VM; not timing evidence)

Every file here comes from the cloud-agent VM, which has no Sage. These files
are exactness and count checks. Any per-call time quoted from here is only an
indication; the Tier 1 run decides.

| file | what | outcome |
| --- | --- | --- |
| `local_replay.py`, `local_replay_archived.json` | `tauDlp`'s control flow in pure Python (PyBackend arithmetic of `rho_frob.py`) + the native solve, on the ten archived scalars with the archived P, λ and rng seeds; the first 300 systems are also checked against a pure-Python S3 evaluation of all 4,096 pairs | targets, gb_calls, spurious, relations and log equal run 38520305068's tau6 rows on 10 of 10 |
| `local_panel.py`, `local_panel.json` | the same on the 16 held-out points | 16 of 16 logs verified; 5,213 solve calls per ECDLP on average |
| `multi_survey.py`, `multi_survey.json` | every (xR, j), exhaustive: systems with two or more solutions, by shift | 2,375 of 9,961,472; 2,001 are shift-0 swaps (a, b), (b, a); 374 are not (4 at shift 0, 370 at shifts 1-18, at most 4 solutions) |
| `multi_calls.py`, `multi_calls.json` | every multi-solution system the candidate meets on the 16 panel points and the 10 archived scalars, with the base membership of each solution | 26 calls, all shift-0 swaps; so the variety order cannot change a count, a relation or a matrix row on this panel |
| `synthetic_receipt.py` | fake rows to test the plumbing of `verify_receipt.py` (a passing receipt and one with a broken gate) | the passing receipt gives a verdict; the broken one is invalid |

Native per-call cost through ctypes was about 14 µs (5 rounds of 20,000
random systems, `time.process_time`). The archived Sage solve took 7.40 ms
per call, but on another host.

The native unit tests (`cargo test --release` in `../native`) pass 3 of 3:

- the field multiplication;
- solve = direct form = brute force on 400 random systems;
- the four known two-solution systems.
