# Lean check

- Toolchain: `leanprover/lean4:v4.35.0-rc4`.
- Mathlib: `021c46bdd042f67b538b9f9871d556a93713a9a9`, pinned in the Lake manifest and package declaration.
- Command: `cd experiments/xedni-point-lift-shift-20261115/formal && lake build PointLiftShift`.
- Outcome: exit 0; `Build completed successfully (9040 jobs)` in `build-output.txt`.
- Both `#print axioms` outputs report only `propext`, `Classical.choice`, `Quot.sound`.
- No `sorry`, `admit`, `sorryAx`, custom claim axioms, or native evaluation proof occurs in the theorem source.
- `lean4checker --fresh` is unavailable on this host.
- The theorem proves existence. The exact minimal representative and its height bound are replayed by the finite-panel audit and identified separately in `PROOF_MAP.md`.
