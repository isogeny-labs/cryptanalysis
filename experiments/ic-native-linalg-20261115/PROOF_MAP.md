# Native IC algebraic invariant proof map

Lean 4 `v4.35.0-rc4`, mathlib commit
`021c46bdd042f67b538b9f9871d556a93713a9a9`.

The five declarations in `ICNative.lean` check the algebraic identities used
by the implementation. The module was compiled to an `.olean`; the final
command and dependency revisions are recorded in `formal-receipt.json`.
`lean-check.log` contains the `#print axioms` results. The declarations use
only `propext` and, for four declarations, `Quot.sound`. There are no claim
axioms, incomplete proof terms or native-evaluation shortcuts.

| Implementation invariant | Lean declaration | Hypotheses and scope |
| --- | --- | --- |
| Initial Euclidean modulus row | `ICNative.euclid_initial` | Any natural modulus p and integer input; p casts to zero in ZMod p |
| Euclidean remainder/coefficient update preserves congruence | `ICNative.euclid_step` | Two current congruences; arbitrary integer quotient k; exact ring arithmetic |
| A forest edge determines the child affine expression | `ICNative.tree_edge_substitute` | Parent affine expression and one edge equation, over any commutative ring |
| Substituting two forest expressions preserves a cycle equation | `ICNative.cycle_row_substitute` | Both affine expressions share a root, over any commutative ring |
| Extracting the log from a signed rational decomposition | `ICNative.rational_log_extract` | Commutative group, certified numerator/denominator powers, exact split a=b*(h*g^e); exponent identity over integers |

The final declaration applies to the signed denominator: its exponent B
includes the sign logarithm when the denominator is negative. The program
subtracts that sign logarithm as well as the absolute-denominator factor logs.

Formalization is **partial at the program level**. These lemmas do not
formalize the C memory model, graph traversal and component assignment,
Euclidean termination and size bounds, the signed 128-bit machine bounds,
the smoothness factorization loop, or the bridge from verified field-element
factor logs to the abstract group hypotheses. The exhaustive projection and
700,000 reconstruction tests check the implementation independently of these
lemmas; they do not replace those remaining formal obligations.

Readable preservation argument: each forest edge has an auxiliary variable
with coefficient 1. Solving that equation substitutes an affine expression
for the child, with the opposite root sign. Repeating this leaves one root
variable per component. Substitution into every original relation yields
the reduced rows; conversely, a solution of those rows extends along the
forest to a solution of the original relations. Self-loops and odd cycles
retain coefficient 2 on a root. No division by 2 or field assumption is
used in this transformation, which is why the exhaustive test also covers
the composite moduli 4 and 6.

For rational reconstruction, maintain r_i=t_i*value modulo p and apply the
Euclidean update simultaneously to r_i and t_i. The program stops when the
positive remainder is at most floor(sqrt(p)). The previous remainder is
larger than that bound; the usual adjacent-convergent determinant identity
bounds the new denominator by p/(floor(sqrt(p))+1). The determinant bound
and loop termination have an executable check in this experiment and remain
outside the checked Lean declarations above.

To replay in an existing environment with the pinned dependencies:

```sh
lake env lean --root=/absolute/path/to/proof-directory -o /tmp/ICNative.olean /absolute/path/to/proof-directory/ICNative.lean
```

The included `lakefile.toml` and `lean-toolchain` also allow creating a fresh
matching environment with `lake update` and `lake build ICNative`.
`lean4checker` was unavailable on this host; no fresh-checker result is claimed.
