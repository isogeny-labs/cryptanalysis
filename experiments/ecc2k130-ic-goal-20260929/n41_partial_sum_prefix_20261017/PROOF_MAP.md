# Proof map

| Result | Lean declaration | Hypotheses and bridge | Status |
| --- | --- | --- | --- |
| An exact common point has a common key under any coordinate-prefix map | `PrefixGate.shared_prefix_of_exact_match` | Two finite lists of points, one point in both, and an arbitrary map to keys | Checked in `PrefixGate.lean` |
| Disjoint key sets certify an empty exact intersection | `PrefixGate.no_exact_match_of_disjoint_prefix` | Finite lists and no shared mapped key | Checked in `PrefixGate.lean` |
| The frozen N41 half-code family has 417,024 admissible triples per side, zero exact common points, and the recorded prefix intersections | No Lean import of the field/group enumeration | Fixed `GF(2)[t]/(t^41+t^3+1)`, curve `y²+xy=x³+1`, source table and public raw target; native producer and independent checked Sage replay | Independently computationally checked in `half_result.json` and `audit_result.json` |

The generic theorem applies with `α` equal to curve points and `keyOf` equal to the top `k` bits of the point's encoded x-coordinate on the nonidentity chart. The native and Sage programs explicitly count identity cases; both count zero in this panel. The finite point lists and numerical prefix counts are not embedded as Lean data.

The toolchain is pinned by `lean-toolchain` to `leanprover/lean4:v4.34.1`. `lean PrefixGate.lean` exited zero; `lean_check.stdout.txt` reports `propext` and `Quot.sound` for both declarations. The source contains no `sorry`, `admit`, custom axioms, or native-evaluation proof. `lean4checker --fresh` was unavailable locally. The first build failed because `prefix` is a Lean keyword; its original source and compiler output are retained separately.
