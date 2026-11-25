# The rational-kernel isogeny as a point bridge

## Exact construction

Let `E/F_p` have prime order `r != p`, and let `pi` be Frobenius with trace `t = p + 1 - r`. The endomorphism `phi = 1 - pi` has

```text
deg(phi) = (1 - pi)(1 - pi_bar) = p + 1 - t = r,
ker(phi) = E(F_p).
```

It is separable: Frobenius has zero differential and `1 - pi` has nonzero differential. Thus this is an explicit degree-`r` isogeny with the whole rational point group as kernel. On the P-192 curve, direct integer arithmetic gives `t = 31607402316713927207482677199`, `p mod r = 31607402316713927207482677198`, and `deg(phi) = r = 6277101735386680763835789423176059013767194773182842284081`. These equalities are exact arithmetic checks, not timing measurements. [pcc:unverified]

The map is cheap to describe and evaluate using Frobenius and one group subtraction on a general extension-field point. On a rational point it evaluates to `P - pi(P) = O`. In particular, `phi(G) = phi(Q) = O` for every ECDLP pair `Q = [d]G`; this map loses the target distinction completely. A lower bound on the degree of a noninteger endomorphism therefore does **not** by itself imply a lower bound on evaluation time. The degree-`r` map here is the counterexample to that inference, while its restriction to `E(F_p)` explains why it gives no scalar information. [pcc:unverified]

## Dual map and the surviving line

The dual endomorphism is `phi_hat = 1 - pi_bar`, with `phi_hat * phi = [r]`. Since `pi * pi_bar = [p]`, Frobenius acts as `1` on the rational `r`-torsion line and `pi_bar` acts there as `p mod r`. Hence

```text
phi_hat(P) = [1 - p]P,                 P in E(F_p),
phi_hat(Q) = [d]phi_hat(G).
```

For P-192, `gcd(1 - p, r) = 1`; the dual therefore permutes the rational group by a **known** scalar. Its kernel is the other Frobenius eigenline, where Frobenius acts as `p mod r`. Transporting both marked points through the dual preserves their unknown ratio. A cross-comparison between differently transported `G` and `Q` would have to find a point collision; the class-group relation alone does not supply one. [pcc:unverified]

The integer and embedding-degree checks can be replayed without elliptic-curve software:

```python
from math import gcd
from sympy import isprime

p = 6277101735386680763835789423207666416083908700390324961279
r = 6277101735386680763835789423176059013767194773182842284081
factors = {2: 4, 5: 1, 2389: 1,
           9564682313913860059195669: 1,
           3433859179316188682119986911: 1}
assert all(isprime(q) for q in factors)
assert r - 1 == __import__('math').prod(q**e for q, e in factors.items())
assert 1 - (p + 1 - r) + p == r
assert gcd(1 - p, r) == 1
k = (r - 1) // 10
assert k.bit_length() == 189 and pow(p, k, r) == 1
assert all(pow(p, k // q, r) != 1 for q in factors if k % q == 0)
```

The last two assertions establish `ord_r(p) = k`, using the prime factorization of `k`. This is a producer arithmetic check, not independent PCC verification. [pcc:unverified]

## The preimage torsor retains the point, but needs orientation

There is an exact point-dependent lift, even though `phi` annihilates rational points. Since `phi=1-pi` is a separable isogeny, every `Q in E(F_p)` has geometric preimages. Choose any `T` with `phi(T)=Q`. Then `pi(T)=T-Q`, and because `Q` is Frobenius-fixed, induction gives

```text
pi^m(T) = T - [m]Q.
```

When `Q` has order `r`, these are `r` distinct points for `0 <= m < r`, and `pi^r(T)=T`. Thus every such `T` has field of definition **exactly** `F_(p^r)`, and Frobenius acts on the preimage fiber as one `r`-cycle. The same unlabelled cycle occurs for every nonzero rational `Q`; its cycle type carries no scalar label. An explicit extension-field representation of a preimage has degree `r`, while a symbolic description by the equation `phi(T)=Q` does not supply an orientation or a cheap comparison algorithm. [pcc:unverified]

Equivalently, the connecting class of `Q` in `H^1(F_p, ker(phi))` is represented at Frobenius by `pi(T)-T=-Q`. Under the identification `ker(phi)=E(F_p)=<G>` and `Q=[d]G`, that value is `[-d]G`. Writing it as the integer `-d mod r` requires the unknown coordinate relative to `G`. This is a **point-dependent relation containing `d`**, but its direct cohomological representation has not reduced the computation. The earlier [prime-division Frobenius-torsor proposal](https://github.com/isogeny-labs/crypto-autoresearcher/blob/main/ledger/proposals/IDEA-20260906-a3e96c.yaml) studies the same orientation issue for a different division map; this paragraph specializes it to `1-pi` and gives the exact field degree. The [formalized `1-pi` kernel and degree](https://taucetiproject.org/docs/TauCeti/AlgebraicGeometry/EllipticCurve/Isogeny/OneSubFrobenius/Basic.html) agree with the elementary identities above. [pcc:unverified]

## Cost and scope gate

This is a point-sensitive ideal of norm `r`, but it does not produce a factor-base relation containing `d`: one direction annihilates all rational points and the dual is known scalar multiplication on them. Constructing a kernel polynomial or an explicit degree-`r` rational map would add work without changing those restrictions. The exact P-192 embedding degree `ord_r(p) = (r - 1)/10` also makes direct access to the complementary torsion line an extension-field problem of 189-bit degree. The earlier factorization is in `crypto:research/notes/cm-isogeny/RESEARCH_NIST_CYCLOTOMIC_POINT_HEIGHTS.md`; this screen independently checked its product, factor primality, and the order test. [pcc:unverified]

This gate applies to `1 - pi` and its dual on a prime-order rational group. It is not a lower bound on all coordinate-dependent isogeny constructions. A successor must specify a target-dependent invariant that survives transport, then charge its evaluation, relation yield, and full single-target recovery against rho. [pcc:unverified]

Producer claims: `PCC-20261124-f14459` for the isogeny restriction and `PCC-20261124-f773c1` for the preimage orbit (both unverified). [pcc:unverified]
