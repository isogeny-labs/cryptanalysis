# Frozen Gaussian-matrix replay on the seven-pair public formula

CryptoMiniSat's first pass over the seven-pair N131 ordinary-point XCNF
discarded seven `3315 × 9132` XOR matrices under its default 2,000-row and
1,000-column limits. This replay keeps the exact public-point XCNF, solver
binary, one worker, 300 CPU-second search cap, 4,500-second wall cap, and
4-GiB combined RSS cap; it raises the matrix limits to 4,000 rows and 10,000
columns and permits seven matrices. The `44172 × 101564` matrix remains
outside those limits. The test asks whether enabling the seven medium-sized
XOR matrices changes ordinary-point search behavior under the same cap.

Run from the repository root with its selected Python 3.9 environment
(including `psutil`):

```sh
python3 -B experiments/ecc2k130-ic-goal-20260929/n131_w18_four_seed_sevenpair_gauss_20261011/replay.py freeze
```

Freeze while the original raw XCNF is present to save its byte hash and the
exact solver settings. Wait for the original run's audited terminal receipt.
Then invoke the same path with `run` in place of `freeze`. The runner
restores the audited formula bytes from its compressed archive, checks the
frozen hash, and launches one solver under the declared limits. It preserves
the complete solver streams, CPU/wall and memory receipt, and any SAT model's
full CNF/native-XOR clause check. A SAT model still needs independent Sage
group replay before it contributes an IC relation.

This is a solver-stage diagnostic on the same public target. Its
`candidate_id` stays `null`; the complete single-target online IC and rho
comparison requires factor logs, final matrix solution, target recovery,
and paired rho timing.
