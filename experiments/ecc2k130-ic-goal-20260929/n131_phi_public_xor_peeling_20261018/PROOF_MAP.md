# Proof map

The abstract structural theorem is [Peel.lean](Peel.lean), compiled with
Lean 4.34.1 pinned in [lean-toolchain](lean-toolchain). Run
`lean Peel.lean`; the retained build and `#print axioms` output are in
[lean_check.log](lean_check.log). `lean4checker --fresh` was unavailable.

| Mathematical result | Lean declaration | Exact hypotheses and verification |
| --- | --- | --- |
| A fresh XOR pivot can be solved for either right-hand side | `XorPeel.xor_twice` | Two arbitrary Boolean values; checked, no axioms |
| A finite triangular fresh-pivot system has a solution for every free-interface assignment | `XorPeel.interface_surjective` | Arbitrary free-input type, arbitrary right-hand sides and tail functions depending on later pivots and the free input; checked, standard `propext` only |

The readable proof solves rows in reverse peel order. A pivot variable occurs
in exactly one active row. Later rows do not depend on that pivot; after
solving the later rows, set the pivot to the row's right-hand side XOR the
known remainder. Induction gives a solution for every interface assignment.

The computational bridge from the concrete 282,598-variable XCNF to the
Lean `Tri` representation is partial: the producer and independent auditor
establish that every concrete XOR row has a fresh noninterface pivot under
their recorded peel orders, and the auditor reverse-solves and replays all
rows for three interface assignments. The full concrete parser, pivot-order
certificate and curve-level CNF semantics are not formalized in Lean. The
abstract theorem does not assert that the full CNF formula accepts any
particular prefix.
