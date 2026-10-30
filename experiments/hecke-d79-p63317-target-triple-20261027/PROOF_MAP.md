# Proof map

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| A verified three-term group equation transports through an additive map | `TargetTriple.triple_transport` | Abstract operations, map preserving addition, and `Q=(B₇+B₂₈)+B₂`; fully checked with no axioms |
| The retained witness gives scalar 973 modulo 2531 | `TargetTriple.scalar_certificate` | Exact anchored logs 2266, 169 and 1069; fully checked with no axioms |

The written proof uses the independently checked group equation `Q=B₇+B₂₈+B₂`. Applying the projected-log homomorphism yields the sum of the three pinned class logs. Their sum is 3504, which reduces to 973 modulo 2531. The independent Sage audit checks the exact point equation, all six probes in the frozen order, and `973T=Q`.

Full geometric formalization remains **partial**: Lean does not yet define the p63317 curve, the projected class points or the group-law calculation for this witness. The exact `79,040`-pattern coverage count and its 28-element complement are exhaustively checked by Sage but are not yet Lean declarations; formalizing the list-to-group enumeration is the outstanding finite proof obligation. The conditional transport theorem and scalar arithmetic contain no `sorry`, `admit`, `sorryAx`, custom research axioms or native-evaluation bypasses.

The toolchain is pinned to `leanprover/lean4:v4.35.0-rc4` with no external dependencies. Run `cd formal && lake build`; `formal/build-output.txt` retains the successful build and `#print axioms` output. `lean4checker --fresh` was unavailable on this host.
