# Ramified degree-five orbit gate

## Exact scope

The degree-five horizontal map in the P-192 S5 screen cannot be iterated into a noninteger self-map using only degree-five horizontal edges. The same is true for the `p=1009`, `r=1069` source used by the three-summand panel. This is a statement about pure degree-five paths through curves with maximal CM order; it leaves mixed-degree paths and coordinate-dependent relations open. [pcc:unverified]

For P-192, `p=6277101735386680763835789423207666416083908700390324961279` and `r=6277101735386680763835789423176059013767194773182842284081`. The trace is `t=p+1-r=31607402316713927207482677199`, and the fundamental Frobenius discriminant is

```text
D = t^2 - 4p
  = -24109379060336110122544161233113975664949272517896865359515.
```

Here `v_5(D)=1`, so 5 ramifies in the maximal order: `(5)=𝔭_5^2`, with one prime ideal of norm 5. The earlier fixed source has `D=-555`, also fundamental with `v_5(D)=1`. For either discriminant, an element of norm 5 cannot exist: writing a noninteger element as `(a+b√D)/2` with `b≠0` gives norm `(a²+|D|b²)/4 >= |D|/4 > 5`; an integer has square norm. Thus `𝔭_5` is not principal. [pcc:unverified]

Every horizontal degree-five edge corresponds to `𝔭_5` (up to isomorphism). A pure length-`e` path corresponds to `𝔭_5^e`. For even `e`, this is the principal ideal `(5^{e/2})`, so any associated endomorphism is scalar multiplication by `±5^{e/2}` (the only CM units are `±1`). For odd `e`, the ideal is not principal, so the path does not return to an isomorphic curve. In particular, the two-edge trip via the dual is `[5]` up to isomorphism and sign. No finite pure degree-five path supplies the noninteger same-curve action that the APS-E3 automorphism orbit uses. [pcc:unverified]

This strengthens the generic norm-length observation for this particular prime. A noninteger element has norm at least `|D|/4`, which by itself would require at least 83 degree-five factors on P-192 because `4·5^82 < |D| <= 4·5^83`. Ramification gives the stronger pure-path conclusion above. Neither statement is a universal evaluation-time lower bound: a map with large degree can have a compact description, and paths involving other prime degrees are outside this gate. [pcc:unverified]

## Independent finite-field check

Using the checked Sage launcher, the following read-only check counts rational degree-five isogenies and compares source and codomain `j` invariants. It separately confirms that the map used in each screen changes the curve. The ideal argument above supplies the conclusion for arbitrary pure degree-five path length. [pcc:unverified]

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import EllipticCurve, GF
cases = [
    (1009, 4, 10),
    (6277101735386680763835789423207666416083908700390324961279,
     -3, int('64210519E59C80E70FA7E9AB72243049FEB8DEECC146B9B1', 16)),
]
for p, a, b in cases:
    E = EllipticCurve(GF(p), [a, b])
    edges = E.isogenies_prime_degree(5)
    print(p, len(edges), int(E.j_invariant()))
    for phi in edges:
        C = phi.codomain()
        print(int(C.j_invariant()), E.j_invariant() == C.j_invariant(),
              len(C.isogenies_prime_degree(5)))
PY
```

Observed output:

```text
1009 1 1003
692 False 1
6277101735386680763835789423207666416083908700390324961279 1 6234286251230310114240839169629130138801351179850969208331
534056218588708780684065490900922064137428911222302036501 False 1
```

The APS-E3 study uses a same-curve automorphism of degree one. On these two maximal-order curves the degree-five horizontal map lands on a different `j` invariant, and its pure degree-five return gives an integer scalar. A successor would need a mixed-degree pointed construction or a relation across distinct curves that depends on the coordinates of the supplied target, then a full setup-charged relation and solver cost comparison against the existing APS contract. [pcc:unverified]
