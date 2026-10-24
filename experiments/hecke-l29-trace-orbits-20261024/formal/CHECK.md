The module was checked with Lean 4.35.0-rc4 (commit `c29b6dda4f7c20e3eeaa717c4e565663c5cfa364`) and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`.

From `/Volumes/SSD990/cryptanalysis/experiments/hecke-two-sheet-small-order-20261023/formal`, whose local Lake environment uses those pinned revisions:

```sh
lake env lean /Volumes/SSD990/cryptanalysis/experiments/hecke-l29-trace-orbits-20261024/formal/MomentTrace.lean
```

The command completed with exit code 0. Its five `#print axioms` lines are saved in `lean_check.txt`. The source contains no `sorry`, `admit`, `sorryAx`, research axiom, or native-evaluation shortcut. `lean4checker --fresh` was not installed on this host. The finite degree-29 field computations and exact matrix rank are independent external certificates, not Lean theorems in this module.
