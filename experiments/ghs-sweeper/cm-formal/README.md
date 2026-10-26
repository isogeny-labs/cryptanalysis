# Partial CM arithmetic proof

Pinned Lean 4.34.1, no external packages. Run `lake build`. Each declaration
prints its axioms; the full repository gate audits all four transitively,
including the generated `valid.eq_1` equation theorem (five in total).
No sorry, custom claim axiom or native-decision trust is used.

| Written claim | Lean declaration | Exact formal scope |
|---|---|---|
| Sorted positive degree tuples have a<=17, b<=26 | `sorted_bounds` | all natural a,b,c of sum 53 |
| No bounded tuple passes norm membership and CM divisibility | `finite_exclusion` | Fin18 x Fin27, norm witnesses in the specified integer rectangle |
| Natural-number lift of the finite exclusion | `no_admissible_partition` | every sorted positive tuple of sum 53, under the explicit bounded norm-membership hypotheses |
| No integral cube trace for norm eight | `no_cube_trace` | u=-5..5, both traces +/-35 |

The first and third use only the standard foundations propext,
Classical.choice and Quot.sound. The other two use no axioms.
Verification receipts are in `../quartic-cubic-checks/`.

The full written geometric result is preserved in
`../CUBIC_CM_DISCRIMINANT.md`. Its missing formal bridges are: unbounded
integer witness bounds; ordinary elliptic endomorphisms and etale 2-adic
Tate modules; degree as CM norm; the rational Hom-space discriminant
argument; unique polarized splitting and Frobenius permutation; restriction
simplicity; quotient construction and arithmetic Torelli. None of these
geometric conclusions is assumed as a custom Lean axiom. The formalization
is partial and does not certify a source-to-quartic map.
