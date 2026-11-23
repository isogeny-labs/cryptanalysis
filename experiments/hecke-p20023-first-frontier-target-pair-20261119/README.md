# A fresh p20023 first-frontier target and same-point rho pair

The prepared 1,760-log first-frontier table recovers a fresh public target in the prime-order 4,021 subgroup after **two additive shifts**. The frozen public point `(2977,7768)` is outside the table. Lookup returns scalar `495 mod 4021`, and two one-target Pollard rho runs on that same point return 495. The accepted Sage build independently replays every prepared log, the target selection, and all four run answers.

The experiment extends the [first natural frontier](../hecke-natural-prefix-20261024/RESULT.md), whose previous frozen target was a direct table hit. `protocol.json` fixes input artifact digests, the new target seed and rejection rule, operation caps, and alternating run order before execution. `freeze.py` publishes the point, saves a separate known-scalar fixture, and seals protocol and public-point hashes in `pre-run.json`. `run.py` verifies that seal, reconstructs the projected table from the frozen representatives and logs, verifies all 1,760 scalar identities, and reads only the public point for target work. `audit_sage.py` reads the fixture after the runs and checks the result in Sage.

| Stage or run | Exact result |
| --- | ---: |
| Field and curve | `F_20023`, `X₀(11): y²+y=x³−x²−10x−20` |
| Subgroup order | 4021, prime |
| Prepared projected points | 1760, all independently replayed |
| Frozen target | `(2977,7768)`; scalar 495 |
| Connector runs | 3 probes, 2 additions, verified scalar 495 in each |
| Rho runs | 384 walk transitions, 1 collision, verified scalar 495 in each |

The rho transition count excludes seeded-state construction and scalar replay; the online wall interval includes both. Exact nanosecond intervals and prepared-table checking are in `result.json`. These are ordinary-host diagnostics with `candidate_id: null`; they do not establish an isolated CPU speedup. The table's original Hecke relation and linear-algebra preparation costs remain separately recorded in the parent experiment. A subsequent candidate manifest and Tier 1 or Tier 0 paired run are needed for a calibrated timing comparison.

## Proof and reproduction

The existing pinned Lean theorem `ShiftClosure.log_from_generator_shift` proves the structural log-transport identity for a checked additive shift. The present experiment builds and axiom-audits that actual module; `#print axioms` reports `propext`. The finite p20023 curve arithmetic, frozen Hecke rows, prepared-log table, and new public-target replay remain computational certificates, with their exact Lean bridge listed in `PROOF_MAP.md`.

```sh
python3 experiments/hecke-p20023-first-frontier-target-pair-20261119/freeze.py
python3 experiments/hecke-p20023-first-frontier-target-pair-20261119/run.py
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-p20023-first-frontier-target-pair-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-p20023-first-frontier-target-pair-20261119/audit_sage.py
cd /Volumes/SSD990/cryptanalysis/experiments/xedni-lattice-obstruction-20261028/formal
lake env lean /Volumes/SSD990/x011-fiber-multiplicity-worktree-20261119/experiments/hecke-l29-final-kernel-search-20261024/formal/ShiftClosure.lean
```
