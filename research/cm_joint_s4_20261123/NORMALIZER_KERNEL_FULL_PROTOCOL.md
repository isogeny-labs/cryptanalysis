# Frozen full horizontal kernel-normalizer census

The [second-control protocol](NORMALIZER_KERNEL_EQUIVALENCE_PROTOCOL.md)
predeclared a full census if its `D=-163` control and both horizontal
eight-label screens passed. They did: `52/52`, `8/8`, and `8/8`, with
curve orientations `+1`. This addendum freezes the next check before
collecting it. [pcc:unverified]

On the same `p=1009`, `r=1069` degree-five horizontal pair and marked
generators used in the preceding script, evaluate **all** labels
`d=1,...,1068` on both source and endpoint. Use the already committed
`census` implementation in `normalizer_kernel_equivalence.py` at
`1d6657c68`. Retain every kernel sign, normalizer sign, orientation,
negation identity check, and mismatch; no early stopping or selection.
The exact prediction is that one orientation per curve makes
`chi_p(K_{1+pi}(x([d]G)))` equal to
`chi_p(y([d]G)*Phi([d]G))` at every label. [pcc:unverified]

Run from the repository root:

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY' > research/cm_joint_s4_20261123/normalizer_kernel_full_results.json
import json, sys
sys.path.insert(0, 'research/cm_joint_s4_20261123')
from sage.all import GF, EllipticCurve
from normalizer_kernel_equivalence import census
F=GF(1009)
E=EllipticCurve(F,[4,10])
phi=E.isogenies_prime_degree(5)[0]
G=E.gens()[0]
assert int(E.cardinality())==1069
assert tuple(int(v) for v in phi.codomain().a_invariants())==(0,0,0,888,852)
labels=list(range(1,1069))
records=[census('source-1009-full',E,G,labels),
         census('endpoint-1009-full',phi.codomain(),phi(G),labels)]
print(json.dumps({'schema':'normalizer-kernel-full/v1','records':records},sort_keys=True,indent=2))
PY
```

Passing this finite census is evidence for a possible structural
identity, not a proof. The subsequent task is to derive the square
class relation from division-polynomial or isogeny identities and
then price the point evaluation. Even a proved cheap evaluation of
this kernel character would need an additional relation to the
unknown scalar and a full same-target rho comparison. [pcc:unverified]
