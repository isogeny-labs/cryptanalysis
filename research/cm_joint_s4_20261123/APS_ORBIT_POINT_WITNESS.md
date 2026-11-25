# Exact point-dependent orbit witness in the existing APS baseline

## Provenance and scope

The [Crypto APS-E3 implementation](https://github.com/isogeny-labs/crypto/blob/5097d0d45c46c72041ddacca012fe694252ded6d/research/aps_extensions_20261026/README.md) already has a retained fixed-curve transcript with an informative relation across automorphism-orbit blocks. The immutable [producer transcript](https://github.com/isogeny-labs/crypto/blob/5097d0d45c46c72041ddacca012fe694252ded6d/research/aps_independent_replay_20261029/fixtures/orbit3.json) has SHA-256 `77471959a576596d72eb2bc883aff1626b20484d00e5580f4cdd08efcf4a5687`; the [separate affine replay receipt](https://github.com/isogeny-labs/crypto/blob/5097d0d45c46c72041ddacca012fe694252ded6d/research/aps_independent_replay_20261029/validation/replays/orbit3.json) binds that hash and checks one recovery. This is prior work, not a new CM construction. [pcc:unverified]

The curve is `E/F_103: y²=x³+5`, with prime group order `r=97`, generator `G=(2,42)`, and supplied target `Q=(23,92)`. The retained relation uses these three points and public labels:

| Point | `(u,v)` in `P=[u]G+[v]Q` |
| :--- | :--- |
| `(19,90)` | `(13,56)` |
| `(78,6)` | `(67,19)` |
| `(82,23)` | `(93,86)` |

The point sum is the identity. Summing the public labels gives `A=13+67+93≡76 (mod 97)` and `B=56+19+86≡64 (mod 97)`. Hence the *point-dependent* relation is `76G+64Q=O`, with `B≠0`, and the recovered scalar is `-76/64≡17 (mod 97)`; direct multiplication checks `[17]G=Q`. The producer's example passes `(E,G,Q,labels,seed,budget)` to the relation solver and compares the returned scalar to the public fixture answer afterward. Its transcript includes that answer for checking, so source inspection and separate replay are both needed to delimit this evidence. [pcc:unverified]

## Current reproduction

This turn independently rechecked the three labels, point sum, coefficient pair, and final multiplication in Sage. The following fixed arithmetic reproduces the check without invoking the polynomial solver:

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import EllipticCurve, GF
E=EllipticCurve(GF(103),[0,5]); G=E(2,42); Q=E(23,92); r=97
trip=[(19,90,13,56),(78,6,67,19),(82,23,93,86)]
assert E.cardinality()==r
assert all(E(x,y)==u*G+v*Q for x,y,u,v in trip)
assert sum((E(x,y) for x,y,_,_ in trip),E(0)).is_zero()
A=sum(u for _,_,u,_ in trip)%r; B=sum(v for _,_,_,v in trip)%r
assert (A,B)==(76,64) and B!=0
assert (A*G+B*Q).is_zero()
assert (-A*pow(B,-1,r))%r==17 and 17*G==Q
print('order',r,'coefficients',A,B,'recovered',17)
PY
```

I also reconstructed the locked standalone replayer from `crypto` commit `5097d0d45c46c72041ddacca012fe694252ded6d` in a temporary directory and ran it on that exact producer JSON. It accepted one attempt, checked all nine labelled base points and three coordinate sets, and verified one recovery. Its own receipt says `enumeration_completeness_verified=false` and `sampling_deadlines_and_costs_verified=false`. The replay therefore certifies the supplied witness within its bounded contract, not a complete cost or large-curve solve. [pcc:unverified]

## Consequence for this PR

This supplies a precise baseline for the first requested kind of evidence: a relation involving a supplied target through nonzero `B`, found by coordinate constraints and independently checked on a fixed public instance. It uses the degree-one automorphism of a special curve. The [P-192 ramified-five gate](HORIZONTAL_FIVE_ORBIT_GATE.md) explains why that orbit cannot be copied through the degree-five horizontal edge, while the [same-base transport theorem](TRANSPORTED_RELATION_GATE.md) explains why transporting these nine labelled points alone cannot add relations. A CM-specific successor still has to change the point-dependent construction or reduce its fully charged cost, and compare it against the matching non-CM method and rho on identical targets. [pcc:unverified]
