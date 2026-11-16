# Lean check

- Toolchain: `leanprover/lean4:v4.35.0-rc4` (`lean-toolchain`).
- Mathlib revision: `021c46bdd042f67b538b9f9871d556a93713a9a9` (`lakefile.toml` and `lake-manifest.json`).
- Command: `cd experiments/xedni-integral-chord-filter-20261115/formal && lake build IntegralChord`.
- Result: exit 0, `Build completed successfully (9040 jobs)`, retained in `build-output.txt`.
- `#print axioms` is executed for all five declarations in `IntegralChord.lean`; each reports only `propext`, `Classical.choice`, and `Quot.sound` in the build output.
- Source has no `sorry`, `admit`, `sorryAx`, custom claim axiom, or native evaluation proof.
- `lean4checker --fresh` is unavailable on this host.
- `integer_slope_of_group_relation` proves the central filter directly from Mathlib affine elliptic-curve group law, nonsingular points, distinct x coordinates, and integral `a₁,a₂,x₁,x₂`.
