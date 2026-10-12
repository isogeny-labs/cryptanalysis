# Ten-pair balanced-tree proof map

`BalancedTen.ten_sum_eq_serial` in [BalancedTen.lean](BalancedTen.lean)
proves that the exact nine-link tree in `tenpair.py` computes the serial
ten-point sum for any binary operation that is associative and commutative.
The theorem quantifies over the carrier, operation, both laws, and all ten
inputs. The final tree link puts the fifth pair ahead of the first four, so
commutativity is necessary for this exact wiring. Elliptic-curve point
addition supplies both laws. No field, subgroup, Frobenius, or factor-base
assumption is hidden in the theorem.

`lean-toolchain` pins Lean 4.34.1 with its bundled `Std`. Build with
`lean BalancedTen.lean`; `lean_check.txt` records the successful build and
`#print axioms`, which reports only standard `propext`. `lean4checker --fresh`
was unavailable on this host. The source contains no `sorry`, custom axiom,
or native-evaluation step.

The theorem establishes the group-sum topology. A full formal proof that
every Boolean XCNF row encodes the corresponding Koblitz point-addition link
is still open: it needs a Lean definition of the polynomial-basis field,
half-trace reciprocal link, selector domain, and emitted circuit semantics.
The complete constructed Boolean assignment is checked against every clause
and native XOR row in `control_result.json`; the signed point sums and
cofactor-four projection are independently replayed by checked Sage in
`sage_audit_result.json`. These executable checks do not replace that
missing formal bridge.
