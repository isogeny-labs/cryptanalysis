# Proof map for adjacent-image factor-base expansion

Let `tau(P)` be coordinatewise squaring on the exact Koblitz curve
`y²+xy=x³+1` over `GF(2^131)`. For a nonexceptional point, the prior
[adjacent Frobenius proof](../n41_n131_adjacent_frob_leaf_20261017/PROOF_MAP.md)
derives `x(P+tau(P))=x(P)+1/x(P)`. Its Lean declarations
`Adjacent.adjacent_polynomial_identity` and `Adjacent.adjacent_parity` were
built under Lean 4.34.1 with an axiom audit. The complete extension-field
group-law bridge remains partial there; the present census checks the
identity through the actual group law on **all 4,134** source representatives,
and [independent Sage](audit_result.json) checks all 4,134 again in a separate
polynomial-field implementation.

The subgroup is cyclic of prime order `r`. Its checked Frobenius eigenvalue is
`lambda=196511074115861092422032515080945363956`. Hence for every subgroup
point `P`, `tau(P)=[lambda]P`, and the group law gives
`P+tau(P)=[1+lambda]P`. The nonzero coefficient modulo `r` is
`196511074115861092422032515080945363957`. This transports the unknown log
of every image point to the same source orbit column. The [prior eigenvalue
audit](../n131_w18_linked_tenpair_public_20261017/lambda_sage_result.json)
checks the exact subgroup generator; the present independent Sage audit
checks the scalar relation on eight frozen representative indices. The
abstract cyclic-group implication is a direct consequence of the group law;
an elliptic-curve Lean declaration for the complete subgroup and map is not
yet available, so the full formalization status is **partial**.

The finite count `B=2,166,216` comes from exact enumeration of both signed
131-step Frobenius orbit x sets and their empty intersection. It is checked
by [census.py](census.py), not by the Lean algebraic identity. The auditor
independently checks the image representative list digest; it does not
independently reconstruct the million-element intersection. The construction
and its empirical count are therefore kept separate from any future SAT
solver, natural relation yield, or final log-rank assertion.
