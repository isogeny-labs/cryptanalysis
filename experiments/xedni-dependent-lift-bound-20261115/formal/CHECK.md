# Formal verification receipt

From this directory:

```sh
lake build XedniDependentLift > build-output.txt 2>&1
```

The command built the copied base module and the new theorem module using
Lean `v4.35.0-rc4` and Mathlib commit
`021c46bdd042f67b538b9f9871d556a93713a9a9`. The retained output
contains `#print axioms` for the new theorem and the 14 reported base
declarations. Only `propext`, `Classical.choice`, and `Quot.sound` occur.
`lean4checker --fresh` is unavailable on this host; the Lean kernel checked
both modules during `lake build`. Run `python3 ../verify.py` to check the
source identity and receipt invariants.
