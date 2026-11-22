# Bounded XOR pivot proof map

The projector eliminates a variable that occurs only in XOR equations by
choosing one equation containing it and adding that equation to every other
equation containing the variable. A proposed pivot is skipped if an affected
row would exceed the frozen width cap. Skipping changes the elimination order
and output size, but does not change the Boolean formula.

For a pivot variable `x`, let its first two equations be `x xor a = p` and
`x xor b = q`. XOR addition replaces the second by `a xor b = p xor q`.
Given this residual equation, the first uniquely determines `x = p xor a`.
Repeating this argument over all rows containing the pivot gives a reverse
lift in the opposite pivot order. Variables absent from both CNF and residual
XOR rows may be assigned zero before lifting.

| Result | Lean declaration | Status and scope |
| --- | --- | --- |
| One XOR row-addition step preserves both equations for every Boolean assignment | `PrivateXorPivot.row_addition` | Checked; all five Boolean inputs quantified |
| One private pivot can be existentially eliminated from two equations | `PrivateXorPivot.elimination` | Checked; all four Boolean parameters quantified |
| One private pivot can be eliminated from an arbitrary list of equations sharing that variable | `PrivateXorPivot.elimination_list` | Checked; all list lengths and Boolean coefficients/parities quantified |
| Repeated elimination over an arbitrary XCNF instance and the exact emitted file | None | Partial formalization; the list/multiset XCNF semantics and bridge from the Python certificate are open. The independent certificate auditor replays all N131 rows but is computational evidence, not a Lean proof. |

Toolchain: `leanprover/lean4:v4.34.1`, commit
`5045d0056413266e57c625dcd7c365b10e377c52`, using the `Std` bundled
with that release. Check with:

```sh
lean PrivateXorPivot.lean
```

The checked output reports that all three declarations depend on no axioms.
`lean4checker` was unavailable on this host. No `sorry`, `admit`, custom
axiom, or native proof evaluation appears in the module.
