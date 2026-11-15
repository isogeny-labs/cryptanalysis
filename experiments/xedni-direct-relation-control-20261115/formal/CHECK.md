# Formal verification receipt

Run from this directory:

```sh
lake build DirectRelation
```

The command completed successfully on the pinned `lean-toolchain` and
`lake-manifest.json` revisions. The exact output is in `build-output.txt`.
All four declarations were audited by `#print axioms` in the built module.
The reported dependencies are standard Lean foundations: `propext`,
`Classical.choice`, and `Quot.sound`. The module contains no `sorry`, `admit`,
custom axiom, or native-evaluation proof step. `lean4checker` was unavailable
on this host; the Lean kernel checked the declarations during `lake build`.

The `relation_reduces` theorem assumes an additive reduction homomorphism.
Constructing that homomorphism for a chosen elliptic model and proving its
good-reduction hypotheses is a separate bridge to the curve instance.
