# Exact three-sum support of the fixed horizontal-edge base

## Scope and count

Use the source curve, degree-5 horizontal isogeny, and eight signed
base points fixed in the [joint S4 panel](README.md). Enumerate the
`C(8+2,3)=120` unordered three-point multisets, allowing repeated
points. Two sum to the identity. Among the other 118 multisets, the
sum-multiplicity histogram is `82` group points with one multiset,
`2` with two, and `8` with four. Hence exactly `92` of the `1068`
nonzero group points have at least one decomposition. The natural
nonzero-query hit probability for this base is `92/1068 = 23/267`;
the mean number of decompositions per such query is
`118/1068 = 59/534`. These are exact finite counts for this one
base, not an asymptotic yield model. [pcc:unverified]

The endpoint base consists of the images of those same eight points.
An independent enumeration of its 120 multisets gives 93 support
points including the identity. For every source support point `P`,
the endpoint multiplicity at `phi(P)` equals the source multiplicity
at `P`. This explicitly checks pointwise transport of the relation
multiset on the finite edge; no additional relations appear at the
endpoint. [pcc:unverified]

The panel's query construction takes `R=[a]G+[b]Q` with `a` uniform
modulo `1069`. Conditional on retaining a nonzero `R`, it is uniform
over the 1068 nonzero group points. The displayed panel then selects
two positive and two negative queries, so its 50% positive share is
a diagnostic sampling choice, not a relation-yield estimate. A
positive query gives the point-dependent equation
`[a]G+[b]Q=P_i+P_j+P_k`; turning such equations into `d` still needs
base logarithms or an alternative low-rank representation, plus
collection and solve costs. [pcc:unverified]

## Fixed-instance replay

The following Sage calculation reconstructs the two bases separately
and checks every multiset count. It is confined to the curve and
base used in this PR. [pcc:unverified]

```python
from sage.all import EllipticCurve, GF
from itertools import combinations_with_replacement
from collections import Counter

E = EllipticCurve(GF(1009), [4, 10])
phi = E.isogenies_prime_degree(5)[0]
B = sorted((P for P in E.points() if not P.is_zero()),
           key=lambda P: (int(phi(P)[0]), int(phi(P)[1])))[:8]
C = [phi(P) for P in B]
indices = list(combinations_with_replacement(range(8), 3))
source = Counter(B[i] + B[j] + B[k] for i, j, k in indices)
endpoint = Counter(C[i] + C[j] + C[k] for i, j, k in indices)
assert len(indices) == 120 and source[E(0)] == 2
assert len(source) == len(endpoint) == 93
assert all(endpoint[phi(P)] == n for P, n in source.items())
nonzero = {P: n for P, n in source.items() if not P.is_zero()}
assert len(nonzero) == 92
assert Counter(nonzero.values()) == Counter({1: 82, 2: 2, 4: 8})
```

This count closes a yield claim for the **transported fixed base**.
It does not compare independently chosen bases on the two curves,
solver representations, or a complete same-target ECDLP cost.
[pcc:unverified]
