# Squaring the ray modulus creates (r)-torsion, but not a point label

The earlier [point-to-ray homomorphism gate](POINT_TO_RAY_HOMOMORPHISM_GATE.md)
rules out an additive map from the prime-order point group into the
class group or the ray class group of modulus `n=(pi-1)` on P-192:
neither has `r`-torsion. This obstruction is **specific to that
modulus**. The next modulus `n^2` has an explicit additive
principal-unit subgroup of order `r`. This is a genuine algebraic
place where a point-to-class bridge could land; the construction
below does not assign a class to an arbitrary supplied point.
[pcc:unverified]

Let `E/F_p` be ordinary with prime `r=#E(F_p) != p`, maximal CM
order `O_K`, fundamental discriminant coprime to `r`, and units
`{+1,-1}`. Put `eta=pi-1` and `n=(eta)`. Since `Norm(n)=r`, `n` is
a prime ideal with residue field `F_r`. The local filtration gives

```text
(1+n)/(1+n^2) ≅ n/n^2 ≅ (F_r,+),
(1+a eta)(1+b eta) = 1+(a+b)eta mod n^2.
```

The ray-class [exact sequence](https://ocw.mit.edu/courses/18-785-number-theory-i-fall-2021/mit18_785f21_lec21.pdf)
injects this subgroup into `Cl_(n^2)(O_K)`: neither `-1` nor any
other nontrivial global unit lies in `1+n`, because `r` is odd.
The whole ray group has order `h_K*r*(r-1)/2`. The prior P-192
class-number bound gives `h_K<r`, so its `r`-primary subgroup has
order exactly `r`. The class of the ideal `(pi)` lies in that subgroup
and corresponds, up to the ray Artin sign convention, to
`pi=1+eta mod n^2`; it generates the subgroup. This is a
canonical **group-theoretic** candidate for the target of an
additive point map. [pcc:unverified]

Fixing `G` and declaring `F(G)=[(pi)]` uniquely extends to a group
isomorphism `F:E(F_p)->Cl_(n^2)(O_K)[r]`. For `Q=[d]G`, it is

```text
F(Q)=[(pi)]^d=[(1+d eta)]  in Cl_(n^2)(O_K).
```

This formula **defines** the desired bridge but does not compute it
from the coordinates of `Q`: writing its principal-unit coefficient
already requires `d`. A smooth-norm relation such as
`alpha=1+pi=2+eta` gives another **known** ray residue;
`alpha/2=1+eta/2 mod n^2`, with its coefficient `1/2 mod r`
known in advance. Collecting such known classes does not identify
the class associated with `Q`. An algorithm would need a
coordinate-dependent way to output an ideal or ray invariant for
that class, followed by a charged way to recover its coefficient.
[pcc:unverified]

There is also a concrete field-size gate for the most direct
class-field evaluation. In the ray class field of modulus `n^2`,
the prime `(pi)` above `p` is unramified and has Artin element of
order `r`. By [Artin reciprocity and the Frobenius residue-degree
identity](https://ocw.mit.edu/courses/18-785-number-theory-i-fall-2021/mit18_785f21_lec21.pdf),
its residue degree is `r`. Thus reducing a generic ray-class-field
generator at `(pi)` entails a residue field with `p^r` elements;
the degree-`r` layer is present even in the `r`-primary quotient.
This prices a **full-field reduction** strategy, not every possible
compressed point-to-ray algorithm. A compressed construction must
explain how it obtains the point-dependent coefficient without
materializing that extension. [pcc:unverified]

The [Sage arithmetic check](squared_ray_kernel.py) verifies the
principal-unit law, ideal norms, and nontriviality on both the
`D=-19`, `p=47`, `r=61` control and exact P-192 parameters. On the
small control it checks all `61^2` coefficient pairs, all
`61` distinct unit labels, and the order of `(pi)` through two
full periods. It also checks `Norm(1+pi)=35=5*7` there. On P-192 it
checks the exact ideal norms and local identities without trying to
construct the ray class field or enumerate `r` elements. These are
arithmetic checks of the proposed codomain, not point-relation or
cost measurements. [pcc:unverified]

The falsifiable next step is an explicit map `M(E,G,Q)` that reads
`Q`'s coordinates and returns a ray-class representative whose
principal-unit coefficient is nonconstant in `d`, without calling a
point DLP or listing the `r` points. It must recover a checked
relation involving `d`, then charge map setup, ideal arithmetic,
coefficient extraction, failed instances, verification, and a cold
same-target rho comparison. The same construction must be tested
against a matched non-CM or known-scalar control so any gain can be
attributed to horizontal structure. [pcc:unverified]

Reproduce the arithmetic check from the repository root:

```sh
/Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/squared_ray_kernel.py
```
