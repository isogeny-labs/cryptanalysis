# Proof map: inverse-output pair equation

| Result | Lean declaration | Exact assumptions and status |
| --- | --- | --- |
| With `ab=1`, the original characteristic-two pair equation `aP + c a² + h=0` is equivalent to `P=c a+h b` | `OutputLinearization.pair_output_linear_iff` | A commutative ring whose addition is self-inverse, with the stated identities for associativity, commutativity, distribution, zero, and one; `ab=1`. Checked in pinned Lean 4.34.1. `#print axioms` reports no axioms. |
| The theorem applies to the exact N131 pair coefficient `c=1+h²`, source product `P(s)`, and standard reciprocal output `a` | Concrete field/circuit bridge | `linear.py` uses the same 131-bit field arithmetic and source product basis as the frozen prior implementation. `linear.py control` checks the old and new equations on all seven selected pairs and evaluates every constructed XCNF clause/XOR row. Formal connection from the abstract ring to `GF(2)[t]/(t¹³¹+t¹³+t²+t+1)` and the Boolean circuit is partial. |
| The new public point lies in the stated prime subgroup and its raw preimage projects to it | Independent Sage fixture replay | `make_target.py` generated the point with the accepted checked Sage launcher; `verify_target.py` independently rechecks seed-to-scalar derivation, generator, public point, `[4]` raw preimage, and reciprocal in `target_replay_result.json`. The generation scalar is retained in `private_fixture.json` and is absent from the SAT formula's assigned inputs. |
| The frozen W20 pair-product basis has rank 19 and codimension 112 | Exact finite GF(2) elimination | `basis_rank.py` records the 19 basis vectors and echelon pivots in `basis_rank_result.json`. A Lean bridge to the concrete 131-bit product-basis generator remains open. |

The theorem proves the complete algebraic equivalence under its stated
inverse and characteristic-two ring assumptions. It does not formalize the
elliptic-curve summation chain, factor-base table, or Sage's concrete binary
field implementation. Those bridges remain explicit proof obligations for
a fully formalized N131 point-decomposition claim.

Run `lean OutputLinearization.lean` with `lean-toolchain`; the executable
version and axiom audit are in `lean_runtime.txt` and `lean_check.txt`.
`lean4checker --fresh` was unavailable on this host.
