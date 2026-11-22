# Lean proof check

`ShiftClosure.lean` was checked with Lean 4 `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`, pinned by `lean-toolchain` and `lakefile.toml`. The command, run from `experiments/hecke-two-sheet-small-order-20261023/formal` where the pinned Mathlib checkout is available, was:

```sh
lake env lean /Volumes/SSD990/cryptanalysis/experiments/hecke-l29-final-kernel-search-20261024/formal/ShiftClosure.lean
```

The saved `lean_check.txt` contains `#print axioms` output. `log_from_generator_shift` uses `propext`; `shift_row_separates_residual` uses `propext` and `Quot.sound`. The module contains no `sorry`, `admit`, custom research axiom, or native-evaluation proof. `lean4checker --fresh` was unavailable in this environment. The finite `F_20023` curve/group encoding, point identities, and the three concrete rank certificates remain external proof obligations; the integer validators check them, but they are not Lean declarations.
