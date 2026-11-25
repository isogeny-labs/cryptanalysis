# A generic fast evaluation of the anti-Frobenius kernel polynomial

## Exact identity

Let `E/F_p: y²=g(x)` be a nonsingular short-Weierstrass curve,
`p>3`, with **odd prime** rational point count `r>=5`. Put
`h=(r-1)/2`, let `pi` be Frobenius, and let `P` be any nonidentity
rational point. Because the group has prime order, `P` generates it.
There is no rational two-torsion. Define the monic polynomials

```text
R(X) = product_{i=1}^h (X-x([i]P)),
K(X) = product_{x in F_p, chi_p(g(x))=-1} (X-x).
```

The first polynomial is independent of the chosen nonzero `P`:
it contains every rational point x-coordinate once. The second is
the x-kernel polynomial of `1+pi`, since `pi(T)=-T` exactly when
`x(T)` is rational and `y(T)` is not. Every field element is in one
of the two root sets, so `R(X)K(X)=X^p-X`. [pcc:unverified]

At `u=x(P)`, differentiating this product gives

```text
-1 = R'(u) K(u).                                           (1)
```

The standard division-polynomial x-difference identity, in the
convention `psi_2(P)=2y(P)`, is

```text
x(P)-x([i]P) = psi_{i+1}(P) psi_{i-1}(P)/psi_i(P)^2
```

for `2<=i<=h`. It follows either from the addition formulas for
division polynomials or the general x-difference formula in
[division-polynomial literature](https://warwick.ac.uk/fac/sci/maths/people/staff/au-yeung/common_valuations_of_division_polynomials.pdf).
None of the denominators vanish because `i<r`. Multiplication over
`i` telescopes:

```text
R'(u) = product_{i=2}^h (x(P)-x([i]P))
      = psi_{h+1}(P)/(psi_2(P) psi_h(P)).                   (2)
```

Combining (1) and (2) yields the **value identity**

```text
K(x(P)) = -psi_2(P) psi_h(P)/psi_{h+1}(P).                 (3)
```

It is valid at every nonidentity rational point on every curve
satisfying the stated hypotheses. It uses neither a smooth norm nor
the CM class group. The [Lauter–Stange division-polynomial recurrence](https://arxiv.org/pdf/0803.0728)
(Theorem 7) evaluates the three required terms at a supplied `P`
with `O(log r)` recurrence steps and constant-size field state;
there is no need to construct the degree-`(2(p+1)-r-1)/2` polynomial
or its isogeny chain. This evaluates the **kernel function**, not the
endomorphism `1+pi` on arbitrary points. [pcc:unverified]

## Reproducible value checks and research consequence

Direct Sage evaluation of both sides of (3) passed on all 60 nonzero
points of the `D=-19`, `p=47`, `r=61` control, all 52 nonzero points
of the `D=-163`, `p=47`, `r=53` control, and the eight predeclared
labels `1,2,3,5,7,11,13,17` on both ends of the fixed `p=1009`,
`r=1069` horizontal edge. These are self-checks of the algebraic
derivation, not an independent proof verdict. Reproduce them from
the repository root:

```sh
/Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/generic_kernel_eval_check.py
```

The [full horizontal character census](NORMALIZER_KERNEL_FULL_PROTOCOL.md)
separately found that the quadratic sign of `K(x(P))` agrees with the
sign of `y(P)*Phi(P)` on all 1068 nonzero points of each endpoint,
after the eight-label confirmation and 52-point second CM control.
That **normalizer sign equality** remains an empirical finite result
here; equation (3) is the proved generic identity. [pcc:unverified]

The earlier [smooth-kernel ray-label test](SMOOTH_KERNEL_CHARACTER_SCREEN.md)
found only `32/60` best-sign agreement with `chi_61(d)` on `D=-19`
and `538/1068` on each `p=1009` endpoint. Thus a fast evaluation of
`K(x(Q))` does not by itself yield the target's scalar character.
Any route through this kernel value still needs a distinct,
coordinate-dependent relation involving the unknown `d`, a reason
horizontal isogenies improve that relation, and a cold full-recovery
comparison against rho. [pcc:unverified]
