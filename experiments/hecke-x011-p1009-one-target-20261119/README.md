# One-target recovery from the p1009 X011 relation lattice

The certified 596-row relation lattice yields logs for all 84 ordered trace-20 fiber points. Reducing the standard basis vectors modulo its saved row-Hermite basis produces a quotient of order 1020; matching each basis coset against multiples of the first basis coset gives the 84 logs. Independent curve multiplication confirms every prepared log. For the frozen public point `(75,527)`, seven additions by `G=(2,155)` reach the fiber, and the prepared log minus seven gives scalar 19 modulo 1020. Two one-target Pollard rho runs on the same point also return 19. The accepted Sage build independently replays the curve order, generator order, all 84 logs, the fixture, and all four run answers.

## Frozen experiment and result

`protocol.json` fixes the point law, HNF digest, algorithms, caps, and run order before execution. `freeze.py` writes the public point and a separate fixture. `run.py` reads only the public point; it derives logs from the saved HNF, scans additive shifts, and runs rho with Floyd collision detection and composite-order congruence handling. It includes scalar replay inside each target interval. The fixture is read only by `audit_sage.py` after the runs.

| Stage or run | Exact result |
| --- | ---: |
| Group and generator order | 1020 |
| Prepared fiber logs | 84 verified |
| Prepared-log derivation | see `result.json`, `prepared_log_derivation_ns`; source loading excluded |
| Connector run 1 | 7 additions, 8 probes, verified scalar 19 |
| Rho run 1 | 258 group steps, 1 collision, verified scalar 19 |
| Rho run 2 | 258 group steps, 1 collision, verified scalar 19 |
| Connector run 2 | 7 additions, 8 probes, verified scalar 19 |

The exact nanosecond intervals are in `result.json`. These are ordinary-host algorithmic diagnostics, with no physical-host or cloud-instance isolation receipt; `candidate_id` remains null. The 84-point prepared table is generated for this fixed p1009 fiber. The present result establishes the finite target connector and same-point correctness comparison. A subsequent benchmark can freeze a complete candidate manifest and isolated timing envelope.

## Reproduction

From this worktree, with the degree-two and relation-lattice inputs checked out:

```sh
python3 experiments/hecke-x011-p1009-one-target-20261119/freeze.py
python3 experiments/hecke-x011-p1009-one-target-20261119/run.py
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-p1009-one-target-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p1009-one-target-20261119/audit_sage.py
cd /Volumes/SSD990/cryptanalysis/experiments/xedni-lattice-obstruction-20261028/formal
lake env lean /Volumes/SSD990/x011-fiber-multiplicity-worktree-20261119/experiments/hecke-x011-p1009-one-target-20261119/formal/ShiftRecovery.lean
```

`formal/ShiftRecovery.lean` proves the structural rule that a prepared log for `P` and an additive shift identity `Q+kG=P` give `Q=(l-k)G`. It is kernel checked; `#print axioms` reports only `propext`. The concrete HNF quotient computation and elliptic-curve certificate are checked computationally and by independent Sage replay; their integration into Lean remains open. See `formal/PROOF_MAP.md`.
