# Proof map

| Result | Formal statement and verification | Concrete bridge |
| --- | --- | --- |
| One product inverse supplies both fixed-seed endpoint inverses and traces | `SharedInverse.product_inverse_gives_endpoint_inverses` and `SharedInverse.shifted_endpoint_trace` in `../n41_n131_shared_pair_inverse_20261017/SharedInverse.lean`; Lean 4.34.1, axiom-free in that experiment's `lean_check.log` | This experiment's full XCNF constructed assignment checks and `audit_sage.py` verify the N41 source and curve instance. The exact binary-field encoding and circuit emission are not yet Lean theorems. |
| Five S3 links sum six pair points | `SixPairJoin.balanced_six_sum`, parameterized by any `Lean.Grind.AddCommGroup`; checked by `lean SixPairJoin.lean` under pinned `lean-toolchain`, `#print axioms` reports no axioms | `audit_sage.py` reconstructs the constructed control; `audit_join_sage.py` checks the public relation on the specified curve. |
| The public target determines the exact complementary left-table key | `SixPairJoin.target_conditioned_lookup`: for all `left right target` in any additive commutative group, `left + right = target ↔ left = target - right`; same axiom-free build | `join_exact.cpp` indexes left triples by exact group point and probes the key `target - right`; `audit_join_sage.py` independently replays the accepted witness. Hashing and input parsing are computationally checked, not Lean definitions. |

The Lean foundations are `Std` and `Init.Grind.Ring.Basic` from `leanprover/lean4:v4.34.1`. The actual theorem module builds and both declarations have `#print axioms` output in `lean_check_final_verified.stdout.txt`; `lean_check_final_verified.stderr.txt` is empty. `lean4checker --fresh` was unavailable in this environment.
