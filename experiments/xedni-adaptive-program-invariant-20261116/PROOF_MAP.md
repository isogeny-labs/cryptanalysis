# Arbitrary-length adaptive group-program invariant

Lean toolchain v4.35.0-rc4; Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9.

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Add/sub command vocabulary and typed finite program | `Op`, `Command`, `Program` | At each step a function of all current labels selects an operation and two existing indices |
| Affine and group command actions | `formOp`, `pointOp` | Ring/field arithmetic and additive group law |
| Operation commutes with affine evaluation and scalar action | `op_commutes` | Field `F`, additive `F`-module `A`, group element `G` |
| Execute the same typed program on group points and symbolic forms | `runGroup`, `runForms` | Bijective encoding `A ≃ L`; arbitrary finite program |
| Full trace representation after any number of steps | `run_invariant` | Initial point and form traces agree under evaluation |
| Public DLP seed representation | `seedForms`, `seedPoints`, `seed_invariant` | Initial points are `G` and `w • G` |
| Full trace representation from the public DLP seed | `dlp_program_invariant` | Same field/module and encoding assumptions; any finite label-adaptive add/sub program |

The program's type tracks the current trace length. Each strategy can inspect
the complete visible label tuple, including repeated labels from earlier
collisions, and choose either addition or subtraction and two prior indices.
The proof of `run_invariant` inducts over the program. At each step the
initial trace equality makes the actual and symbolic visible label tuples
equal, so both executions choose the same command. The `op_commutes` equality
identifies the newly appended point with the evaluated new affine form.
The seed theorem identifies `G` with the constant form and `w • G` with the
identity form.

This is a representation theorem, not a count of first-collision
probabilities. A complete generic-group lower bound still needs a checked
count over random encodings and target scalars through the first collision,
including symbolically identical forms and stopping behavior. The model
provides abstract random labels; it has no concrete curve-coordinate oracle.

`lake build AdaptiveProgramInvariant` completed 3,142 jobs. All twelve new
`#print axioms` reports use only standard Lean foundations (`propext`,
`Classical.choice`, and `Quot.sound` where applicable). The module has no
`sorry`, `admit`, custom research axiom, or native evaluation.
`lean4checker --fresh` was unavailable on this host.
