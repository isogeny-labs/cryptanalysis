# Proof map

| Result | Lean declaration | Hypotheses and verification |
| --- | --- | --- |
| A pair equation transports through a map that preserves addition and negation | `TargetPair.pair_transport` | Abstract groups represented by operations, a map preserving both operations, and the stated group pair relation; fully checked with no axioms |
| The retained witness gives scalar 86 modulo 199 | `TargetPair.scalar_certificate` | Exact class logs 163 and 50, first witness signs `−1,+1`, modulus 199; fully checked with no axioms |

The written proof starts with the independently checked curve-group equation `Q=-B₁+B₄`. Applying the projected-log homomorphism gives `log_T(Q)=-log_T(B₁)+log_T(B₄)`. The pinned class-log receipt supplies 163 and 50, and the Lean arithmetic certificate reduces their signed sum to 86 modulo 199. The independent Sage audit also verifies `86T=Q` and enumerates the same scalar from the public point.

Full geometric formalization remains **partial**: Lean does not define this elliptic curve, the concrete projected points, or the group-law computation proving `Q=-B₁+B₄`. Those are presently checked by independent Sage replay. The abstract transport theorem and exact finite scalar step are faithful to the required hypotheses, without `sorry`, `admit`, `sorryAx`, custom research axioms or native-evaluation bypasses.

The toolchain is pinned to `leanprover/lean4:v4.35.0-rc4` with no external Lean dependencies. Run `cd formal && lake build`; `formal/build-output.txt` records the successful build and `#print axioms` output. `lean4checker --fresh` was unavailable on this host.
