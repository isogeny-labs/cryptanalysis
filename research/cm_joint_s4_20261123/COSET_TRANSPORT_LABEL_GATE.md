# Coset transport and labelled-base gate

## Prior question and fixed-edge screen

The earlier `crypto-autoresearcher` proposal [`IDEA-20260906-5b4930`](https://github.com/isogeny-labs/crypto-autoresearcher/blob/main/ledger/proposals/IDEA-20260906-5b4930.yaml) already identifies the key contrast: an isogeny preserves the point-relation multiset of a transported base, while it may destroy a sparse coordinate description. The [general transport gate](TRANSPORTED_RELATION_GATE.md) formalizes the point side. This note checks only the polynomial-shape side on the degree-five horizontal edge already used by this PR. It makes no claim of a faster solver. [pcc:unverified]

On `E/F_1009: y²=x³+4x+10`, let `φ=E.isogenies_prime_degree(5)[0]`. For each tested divisor `B∈{4,6,7,8}` of `1008`, enumerate distinct multiplicative cosets `V=c μ_B⊂F_1009*`; retain a coset only when every x-coordinate lifts to a rational point of `E`. Its source vanishing polynomial is the two-term `X^B-c^B`. Form the endpoint polynomial `∏_{x∈V}(X-x(φ(P_x)))`, with either lift `P_x` for each x. Direct point evaluation and the rational x-map agree on all retained coordinates. [pcc:unverified]

| `B` | Fully liftable cosets | Source nonzero coefficients | Endpoint nonzero coefficients | Endpoint x collisions |
| ---: | ---: | ---: | :--- | ---: |
| 4 | 23 | 2 each | 5 each | 0 |
| 6 | 5 | 2 each | 7 each | 0 |
| 7 | 1 | 2 | 8 | 0 |
| 8 | 2 | 2 each | 9 each | 0 |

For the first eligible `B=6` coset, `c=179`, the endpoint coefficients from constant through leading term are `[696, 95, 47, 657, 963, 643, 1]` modulo `1009`. All seven are nonzero. This confirms loss of the two-term **coordinate presentation** on these finite cells. It does not establish any change in Gröbner solving degree, elapsed cost, relation yield, or a large-field trend. [pcc:unverified]

Reproduce from the repository root with the checked Sage launcher:

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import EllipticCurve, GF, PolynomialRing
from collections import Counter
p=1009; F=GF(p); E=EllipticCurve(F,[4,10]); phi=E.isogenies_prime_degree(5)[0]
R=PolynomialRing(F,'X'); X=R.gen(); g=F.multiplicative_generator()
for B in (4,6,7,8):
    z=g**((p-1)//B)
    hist=Counter(); first=None
    for k in range((p-1)//B):
        c=g**k; xs=[c*z**i for i in range(B)]
        if not all(E.is_x_coord(x) for x in xs): continue
        ys=[phi(E.lift_x(x))[0] for x in xs]
        assert len(set(ys))==B
        assert all(phi.x_rational_map()(x)==y for x,y in zip(xs,ys))
        src=R.prod(X-x for x in xs); dst=R.prod(X-y for y in ys)
        hist[(sum(bool(a) for a in src.list()),
              sum(bool(a) for a in dst.list()))]+=1
        if first is None: first=(int(c),[int(a) for a in dst.list()])
    print(B, sorted(hist.items()), first)
PY
```

## The APS label cost

The coset is selected by its **coordinates**. Its points do not arrive with public labels `(u,v)` satisfying `P=[u]G+[v]Q`, which the APS single-relation construction requires to turn a zero sum into a scalar equation. In the specific rejection model that samples independent uniform pairs `(u,v)` and keeps `uG+vQ` only if it lands in a preselected point base of size `M`, each draw hits with probability exactly `M/r` and the expected draws to one hit are `r/M`. This is independent of any unknown scalar because a uniform `u` makes `uG+vQ` uniform for each `v`. [pcc:unverified]

The fully signed `B=6` coset above has `M=12` points in the prime-order group of size `1069`, giving `1069/12≈89.08` draws per accepted labelled point under that model. At P-192, even allowing `M=2^45` points, one accepted point would require at least `r/M≈2^147` independent uniform draws in expectation. This is about `2^51.174` times the negation-aware rho reference `sqrt(πr/4)≈2^95.826` in **draw counts**, before group arithmetic or equation solving. The bound applies only to this rejection route; it is not a lower bound on every possible way to construct a coordinate-structured labelled base. [pcc:unverified]

The finite shape result therefore does not itself bridge the APS labels to a class-group or horizontal-isogeny relation. A successor must specify a different label-construction mechanism or show a complete solver gain on a base whose labels are already available, charging setup, rejected samples, failed relations, and the matched same-target reference. [pcc:unverified]
