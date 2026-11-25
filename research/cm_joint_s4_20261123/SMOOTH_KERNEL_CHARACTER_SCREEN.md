# Character of a smooth CM kernel function

## Candidate and exact finite construction

A smooth horizontal chain can give a compact evaluation description for a
high-degree isogeny kernel function. This is a concrete class left open by
the [outer-character degree bound](OUTER_CHARACTER_DEGREE_GATE.md): the
bound concerns rational-map degree, not the cost of a short circuit.
The candidate here is the field quadratic character of the kernel
function for `alpha=1+pi`, evaluated at the supplied point `Q`.
The [generalized division-polynomial construction for arbitrary
isogenies](https://link.springer.com/article/10.1007/s40993-026-00741-2)
provides the relevant kernel divisor and chain rule. The tested
identity is whether its field character, after one global orientation
choice, equals `chi_r(d)` for every `Q=[d]G`. [pcc:unverified]

On a short Weierstrass `E/F_p: y^2=g(x)` with odd prime point count
`r`, the kernel of `1+pi` is the anti-Frobenius group. For its nonzero
points, `pi(P)=-P` means `x(P) in F_p` and `y(P)^p=-y(P)`, so `g(x(P))`
is a quadratic nonresidue in `F_p`. There is no rational two-torsion.
Consequently, for `n=deg(1+pi)=2(p+1)-r`, which is odd in the tested
instances,

```text
K_E(X) = product_{x in F_p, chi_p(g(x))=-1} (X-x),
deg(K_E) = (n-1)/2.                                               (1)
```

The rational function `K_E(x(P))` has divisor
`sum_{T in ker(1+pi), T != O}(T) - (n-1)(O)`, the same divisor as the
unbiased generalized division polynomial for `1+pi`. Thus they differ
by an `F_p` nonzero constant; allowing either global output sign covers
the possible field-character normalization. The function is finite
and nonzero at every nonidentity rational point because `r` is prime
and coprime to `n` in these instances. [pcc:unverified]

On `E/F_47: y^2=x^3+x+38`, `r=61`, `G=(2,1)`, the Frobenius trace is
`-13` and `n=35=5*7`. The 17 nonresidue x-values give the full
35-point kernel, including `O`; every lifted point over `F_(47^2)`
satisfies `P+pi(P)=O`. This is a genuinely smooth noninteger CM
endomorphism, although formula (1) exists for ordinary curves without
using its smooth factorization. [pcc:unverified]

## Exact character census and horizontal control

| Curve and marked generator | `n` | `deg K_E` | Raw agreement with `chi_r(d)` | Best global sign |
| --- | ---: | ---: | ---: | ---: |
| `D=-19`, `p=47`, `r=61`, `G=(2,1)` | 35 | 17 | 32/60 | 32/60 |
| `D=-163`, `p=47`, `r=53`, `G=(19,37)` | 43 | 21 | 24/52 | 28/52 |
| `p=1009`, `r=1069`, source `y^2=x^3+4x+10` | 951 | 475 | 530/1068 | 538/1068 |
| degree-5 horizontal codomain `y^2=x^3+888x+852` | 951 | 475 | 538/1068 | 538/1068 |

All 2,248 tested evaluations are nonzero. The first row rejects the
exact ray-label identity for the smooth `1+pi` control; it is not
repaired by changing the kernel function's global normalization. The
`D=-163` row is a different-order ordinary control, not a paired
isogeny comparison. The last two rows use the **same** 1,068 scalar
labels and a degree-5 horizontal map with kernel polynomial
`x^2+507x+633`. The best orientation ties rather than improving on
the endpoint. The two sign sequences themselves are not conserved:
they agree on 560 labels and differ on 508. These are exact finite
censuses, with no statistical extrapolation to P-192 or timing claim.
[pcc:unverified]

Reproduce from the repository root with the checked Sage launcher:

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import GF, ZZ, EllipticCurve, PolynomialRing, kronecker

def kernel_character(E, G, r):
    p = int(E.base_field().cardinality())
    assert E.cardinality() == r and G.order() == r
    assert tuple(int(v) for v in E.a_invariants()[:3]) == (0, 0, 0)
    F = E.base_field()
    R = PolynomialRing(F, 'X')
    X = R.gen()
    a, b = int(E.a4()), int(E.a6())
    roots = [F(x) for x in range(p)
             if kronecker((x*x*x+a*x+b) % p, p) == -1]
    K = R.prod(X-x for x in roots)
    n = 2*(p+1)-r
    assert n % 2 and K.degree() == (n-1)//2
    signs = []
    for d in range(1, r):
        value = K((d*G)[0])
        assert value != 0
        signs.append(1 if value**((p-1)//2) == 1 else -1)
    truth = [int(kronecker(d, r)) for d in range(1, r)]
    raw = sum(a == b for a, b in zip(signs, truth))
    return n, K.degree(), raw, max(raw, r-1-raw), signs

F = GF(47)
E1 = EllipticCurve(F, [1, 38])
E2 = EllipticCurve(F, [5, 8])
for name, E, G, r in [('D-19', E1, E1(2, 1), 61),
                      ('D-163', E2, E2(19, 37), 53)]:
    n, degree, raw, best, _ = kernel_character(E, G, r)
    print(name, n, degree, raw, best)

F = GF(1009)
E = EllipticCurve(F, [4, 10])
G = E.gens()[0]
phi = E.isogenies_prime_degree(5)[0]
assert ZZ((1009+1-1069)**2-4*1009).is_fundamental_discriminant()
assert [int(c) for c in phi.kernel_polynomial().list()] == [633, 507, 1]
assert tuple(int(v) for v in phi.codomain().a_invariants()) == (0,0,0,888,852)
src = kernel_character(E, G, 1069)
dst = kernel_character(phi.codomain(), phi(G), 1069)
print('source-1009', src[:4])
print('codomain-1009', dst[:4])
print('same_signs', sum(a == b for a,b in zip(src[4], dst[4])))
PY
```

The `D=-19` kernel assertion can be checked separately over `F_(47^2)`:

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import GF, EllipticCurve, kronecker
p=47
E=EllipticCurve(GF(p),[1,38])
EL=E.change_ring(GF(p**2,'z'))
roots=[x for x in range(p) if kronecker((x*x*x+x+38)%p,p)==-1]
for x in roots:
    P=EL.lift_x(EL.base_field()(x))
    assert P+EL(P[0]**p,P[1]**p)==EL(0)
assert 2*len(roots)+1 == 35 == 2*(p+1)-E.cardinality()
print('35 kernel points verified')
PY
```

## Scope of the failed identity

This test rejects the **single** proposed field-character predicate
`chi_p(K_{1+pi}(x(Q)))` as an exact ray label on the finite smooth
control. The candidate is point-dependent and its isogeny kernel is
real; the observed sign does not supply a useful equation in the
unknown scalar. Other smooth principal elements may have different
kernel functions. A combination of functions, a different character,
or a high-degree circuit representing a different ray quotient remains
untested. Any successor needs an exact or predeclared predictive
identity, a matched horizontal versus native control, and a charged
full-recovery comparison with rho. [pcc:unverified]
