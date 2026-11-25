# Same-base relation transport gate

## Point-level statement

Let `H` and `H'` be finite additive groups and let `φ:H→H'` be an injective homomorphism. Fix a labelled list `B=(P_i)` and a target `R∈H`. For every finite index tuple `I`,

```text
sum_{i in I} P_i = R    iff    sum_{i in I} φ(P_i) = φ(R).
```

The same equivalence holds for signed equalities between two lists and for zero sums. The map on index tuples is the identity: each source witness has exactly one transported endpoint witness, including all multiplicities and repeated-index conventions. If each `P_i` carries public labels `(a_i,b_i)` through `P_i=[a_i]G+[b_i]Q`, its transported point carries those same labels relative to `(φ(G),φ(Q))`. Consequently a signed zero sum yields exactly the same public coefficient pair `(A,B)` on both sides. Its informativeness (`B≠0`) and any relation-matrix rank are unchanged. [pcc:unverified]

For the ordinary prime-order curves in this PR, a rational isogeny of degree coprime to the group order restricts to an injection on rational points: a rational kernel point would have order dividing both the degree and the prime group order. The source and codomain have the same point count, so that restriction is a bijection. Thus the theorem applies to the existing degree-five horizontal maps. It also applies to any prime-to-order horizontal chain, regardless of whether the path closes in the class group. [pcc:unverified]

For a uniform source query `R`, `φ(R)` is uniform on the codomain group. The exact support probability, complete multiplicity distribution, and informative relation probability for a **fixed transported labelled base** are therefore equal. The [fixed eight-point enumeration](EXACT_THREE_SUM_SUPPORT.md) checks one instance of this general fact. The result does not compare a newly selected codomain base with a source base; it also says nothing about the cost of constructing the base, evaluating `φ`, or solving its coordinate equations. [pcc:unverified]

## What can still change

An endpoint polynomial presentation can change elimination cost or suppress extraneous algebraic-closure solutions even when the rational point witnesses coincide. This is exactly the possible gain tested by the [source, mapped, and joint systems](README.md); that small repeated panel found no process-level reduction. A different factor-base selection law on the codomain may also change relation supply, but then both the selection/label costs and a size-matched source control must be charged. The theorem only fixes the same-base transport comparison. [pcc:unverified]

The [APS-E3 study in Crypto](https://github.com/isogeny-labs/crypto/blob/5097d0d45c46c72041ddacca012fe694252ded6d/research/aps_extensions_20261026/README.md) already has an informative point relation across automorphism-orbit blocks on a fixed public curve. It is a different base construction. The transport theorem shows that merely adding a horizontal endpoint to that **unchanged labelled point base** cannot improve its relation supply. The remaining CM-specific question is whether a different coordinate-dependent base or a cheaper exact equation solver improves complete cold cost relative to a matched non-CM control. [pcc:unverified]

## Formal scope and reproduction

[`formal/TransportGate.lean`](formal/TransportGate.lean) proves `map_sum`, `relation_iff`, `zero_relation_iff`, and `signed_relation_iff` over arbitrary additive commutative groups, assuming an injective additive map. It imports the minimal additive-group model at `research/base-point-independence-20261108/formal/BasePointIndependence/Core.lean` (SHA-256 `09ec555b36dd89631e30d983ef02d16ad953dd394fbd27e69f1bfd4652fb231d`). The prime-to-order isogeny injection, label propagation, probability statement, and solver-cost distinction are mathematical applications stated here, not formalized elliptic-curve theorems. [pcc:unverified]

With the repository's pinned Lean 4 `v4.34.1`:

```sh
mkdir -p /tmp/cm-transport-lean/BasePointIndependence
lean -o /tmp/cm-transport-lean/BasePointIndependence/Core.olean research/base-point-independence-20261108/formal/BasePointIndependence/Core.lean
LEAN_PATH=/tmp/cm-transport-lean lean -t 0 research/cm_joint_s4_20261123/formal/TransportGate.lean
```

The producer run passed. `#print axioms` reported no axioms for the four transport declarations; an independent PCC verdict has not been issued. [pcc:unverified]
