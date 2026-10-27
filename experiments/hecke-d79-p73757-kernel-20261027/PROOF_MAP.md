# Proof map

| Result | Lean declaration | Exact hypotheses and scope | Status |
| --- | --- | --- | --- |
| A verified group relation maps to a zero relation under an additive, integer-scale-compatible homomorphism | `KernelMechanism.verified_relation_annihilates` | Abstract types `G,H`, zero, addition, integer scaling, map preserving all three, and `relationSum row = zeroG` | Fully checked, no axioms |
| The p73757 projected log vector is nonzero | `FiniteP73757.qLog_nonzero` | The exact 40-entry list generated from the pinned result | Fully checked, no axioms |
| All 706 combined rows annihilate that vector modulo 199 | `FiniteP73757.allRows_annihilate` and 23 `rowChunk*_annihilates` declarations | Exact row coefficients reduced modulo 199 and the exact vector | Fully checked arithmetic; `propext` in assembly theorem |
| The selected 39 rows belong to the matrix | `FiniteP73757.selected_in_allRows` | Selected row indices and exact 706-row list | Fully checked arithmetic; `propext` |
| A 39-by-39 minor is invertible modulo 199 | `FiniteP73757.minor_matches`, `FiniteP73757.inverse_certificate` | Selected rows, 39 pivot columns, explicit inverse | Fully checked arithmetic; `propext` |

The mathematical proof of the rank ceiling is direct. The projected logarithm `φ(P)=log_T(370P)` is a homomorphism on the finite curve group because multiplication by 370 is a homomorphism and the order-199 subgroup is cyclic with generator `T`. For a group relation `Σa_iP_i=O`, the Lean structural theorem gives `Σa_iφ(P_i)=0`. The vector is nonzero because `φ(P₀)=1`, so it lies in the right kernel and rank is at most 39. The modular inverse certificate gives a nonzero 39-by-39 minor, so the combined matrix has rank at least 39. The rank calculation is independently replayed for each support-five arm by the Sage producer and pure-Python auditor.

Full geometric formalization remains **partial**: Lean does not yet define the p73757 elliptic curve, its group law, the concrete point-to-log homomorphism, or the source relation constructor. The Sage and independent pure-Python checks supply those finite bridges. The rank-from-minor and nonzero-kernel linear-algebra implications are written here and verified computationally, but are not yet Lean theorems. No `sorry`, `admit`, `sorryAx`, custom research axiom, or native evaluation bypass is used.

The toolchain is `leanprover/lean4:v4.35.0-rc4`, with no external dependencies. Run `cd formal && lake build`. `formal/build-output.txt` retains the successful build and `#print axioms` output. `lean4checker --fresh` was unavailable on this host. The first build attempt was launched from the parent directory and its error is retained in `formal/build-attempt1.txt`; the subsequent build from `formal/` succeeded.
