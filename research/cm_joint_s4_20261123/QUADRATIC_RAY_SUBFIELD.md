# An explicit quadratic ray subfield and the missing point orientation

## Construction

Let `E/F_p` have prime order `r != p`, fundamental Frobenius discriminant `D=t^2-4p`, and CM field `K=Q(sqrt(D))`, with Frobenius `pi=(t+sqrt(D))/2`. Put `n=(1-pi)`. Since `Norm(1-pi)=#E(F_p)=r`, `n` is a prime ideal of norm `r`. For P-192 and the `D=-19` control below, `r=1 mod 4` and `O_K^*={+1,-1}`, so the relative ray-class kernel has one quadratic character, namely the Legendre character on `(O_K/n)^*=F_r^*` modulo sign. The [ray-class exact sequence](https://ocw.mit.edu/courses/18-785-number-theory-i-fall-2021/mit18_785f21_full_lec.pdf), Theorem 21.8, supplies this kernel. [pcc:unverified]

Consider the quadratic extension

```text
L = K(beta),       beta^2 = 1 - pi.
```

For both curves, an exact number-field calculation gives `Disc(L/K)=n`. Since `n` has odd prime norm, this is tame ramification at `n` and no other relative ramification. The conductor is therefore `n`, by the conductor criterion in [MIT 18.785, Proposition 22.25 and the class-field completeness theorem](https://ocw.mit.edu/courses/18-785-number-theory-i-fall-2021/mit18_785f21_lec22.pdf). Thus `L` lies in the ray class field of modulus `n`. Its character is ramified at `n`, so its restriction to the relative ray kernel is nontrivial and equals the unique quadratic character there. On a principal ideal `(a+b*pi)` coprime to `n`, its relative-kernel residue is `a+b mod r`; the quadratic Artin value is `chi_r(a+b)`. The Artin convention cannot change this sign because a quadratic character equals its inverse. [pcc:unverified]

This subfield is compact. Over `Q`, `beta` satisfies

```text
beta^4 - (2-t)*beta^2 + r = 0.
```

Its coefficients have `O(log p)` bits even though the complete ray class field can be enormous. At the chosen prime `(pi)` above `p`, `beta^2=1-pi=1`, so the two reductions of `beta` are `+1` and `-1`. Trivial Frobenius at this prime makes both available in the residue field; it does not select one for a marked point. [pcc:unverified]

## Exact controls

For `D=-19`, `p=47`, `r=61`, `t=-13`, the quartic is `z^4-15*z^2+61`. The noninteger smooth-norm element `gamma=1+pi` has norm `35=5*7` and ray residue `2 mod 61`. Its prime-ideal factors of norms `5` and `7` have quadratic Artin signs `-1` and `+1`, whose product is `-1=chi_61(2)`. This connects the explicit quadratic subfield to the earlier known-scalar control without assigning a label to a separately supplied point. [pcc:unverified]

For P-192, Sage confirms that `D` is fundamental, `r` is prime, `Norm(1-pi)=r`, and `Disc(L/K)=(1-pi)`. On the odd integer ideals `(3)` and `(7)`, the quadratic Artin signs are `-1` and `+1`, matching `chi_r(3)` and `chi_r(7)`. These are checks of known residues, not tests on an unknown target. [pcc:unverified]

The following Sage calculation reproduces the discriminants and the odd-prime Artin checks:

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import ZZ, QuadraticField, PolynomialRing

instances = [
    ('D-19', ZZ(47), ZZ(61), [3, 7]),
    ('P-192',
     ZZ(6277101735386680763835789423207666416083908700390324961279),
     ZZ(6277101735386680763835789423176059013767194773182842284081),
     [3, 7]),
]
for name, p, r, controls in instances:
    t = p + 1 - r
    D = t*t - 4*p
    assert D.is_fundamental_discriminant() and r.is_prime() and r % 4 == 1
    K = QuadraticField(D, 's')
    pi = (t + K.gen())/2
    alpha = 1 - pi
    R = PolynomialRing(K, 'z')
    z = R.gen()
    L = K.extension(z*z - alpha, 'b')
    assert alpha.norm() == r and L.relative_discriminant() == K.ideal(alpha)
    signs = {}
    for u in controls:
        artin = 1
        for q, e in K.ideal(u).factor():
            F = q.residue_field()
            assert F.characteristic() != 2
            x = F(alpha)
            assert x != 0
            artin *= (1 if x**((F.cardinality()-1)//2) == 1 else -1)**e
        legendre = 1 if pow(u, (r-1)//2, r) == 1 else -1
        assert artin == legendre
        signs[u] = artin
    print(name, {'norm': int(alpha.norm()), 'relative_discriminant_ok': True,
                 'known_residue_signs': signs})
PY
```

The `D=-19` `gamma=1+pi` factor check was also run separately; the script above uses integer ideals to share one reproducible procedure across the two curves. At a prime of residue characteristic `2`, the odd-field Euler exponent used here is invalid, which is why the controls use odd primes. [pcc:unverified]

## The algorithmic gap

A point-labelled embedding of the full ray field restricts to a choice between the two roots of `beta^2=1` at `(pi)`. If an evaluator could assign that sign to `Q=[d]G` relative to `G` from their coordinates, its ratio would be `chi_r(d)`. The [quadratic resolvent](RAY_LABEL_CHARACTER_GATE.md) supplies this transformation law, but its direct target evaluation has `(r-1)/2` terms. The quartic description of `L` removes the need to construct the **full field merely to name the quadratic quotient**; it does not compute the embedding selected by `Q`. A small defining polynomial and a point-to-root evaluator are separate objects. [pcc:unverified]

The field `K=Q(pi)` and the expression `1-pi` arise for ordinary curves generally; this compact subfield construction alone is not an improvement attributable to horizontal isogenies or smooth ideals. The next decisive construction is an explicit, target-dependent map from `(E,G,Q)` to the root choice, with a known-scalar sign control (`G` versus `[3]G` on P-192), an independent finite CM control, a matched ordinary-curve control of comparable size, and a charged cold cost. It must show where the isogeny data change evaluation yield or cost, and how any recovered character information lowers full single-target work below rho; one bit by itself is not an end-to-end result. No novelty claim is made for quadratic class fields or class-field reciprocity. [pcc:unverified]

Producer claim: `PCC-20261124-cc257a` (unverified). [pcc:unverified]
