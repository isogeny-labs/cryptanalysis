# Pinned Hecke theorem build environment

This Lake project pins Lean 4 `v4.35.0-rc4` and Mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9` for the Hecke theorem
modules added after the frozen 96-file Lean corpus receipt.

The `Lean corpus evidence bridge` workflow fetches the pinned Mathlib
cache and runs `tools/lean/current-corpus-gate.py`. That gate continues
to compare the original 96-file evidence with its committed receipt,
then natively builds every additional tracked Hecke `formal/*.lean`
module. It checks that each theorem or lemma has a corresponding
`#print axioms` result and admits only the standard Lean foundations
`propext`, `Classical.choice`, and `Quot.sound`.

The pinned project can also be used locally:

```sh
cd experiments/hecke-432-formal-ci-20261025
lake exe cache get
lake env lean -R /absolute/path/to/cryptanalysis /absolute/path/to/cryptanalysis/experiments/hecke-432-direct-lift-20261025/formal/DirectLiftRank.lean
```

The path arguments in the last command must name the actual repository
root and theorem source being checked.
