# Ray-class reduction audit for the point bridge

## Claim under review

The proposed [CM ray-class obstruction](https://github.com/isogeny-labs/crypto-autoresearcher/blob/main/ledger/proposals/IDEA-20260808-5158fa.yaml) correctly observes that the ray modulus `n = (pi - 1)` makes `pi = 1 mod n`, so the prime over `p` has trivial Artin symbol in the relative ray class extension. It then says that reduction collapses the torsor and predicts one distinct reduced Weber value per level fiber. Its [later rescreen](https://github.com/isogeny-labs/crypto-autoresearcher/blob/main/ideas/rescreen-20260808/slice1.md) checks the splitting argument but does not check this distinctness assertion. The latter assertion is false under the proposal's own prime-to-`p`, good-reduction assumptions. This audit does **not** dispute the trivial Artin symbol or assert an efficient way to label the reduced values. [pcc:unverified]

## Distinctness argument

Let `E` have good ordinary reduction at a prime over `p`, and let `r != p` be the prime order of its rational subgroup. A CM lift has a point `Ptilde` of order `r` reducing to `P`. Reduction on `r`-torsion is injective, indeed an isomorphism over algebraic closures, by the standard good-reduction theorem; see [Snowden, Lecture 8, reduction of torsion points](https://websites.umich.edu/asnowden/teaching/2013/679/L08.html). For a generic CM `j`-invariant, the Weber function is a nonzero scalar multiple of the x-coordinate; see [Jung, Koo, and Shin, equation (2)](https://arxiv.org/abs/1408.5650). Hence, for units `u,v mod r`,

```text
red(h([u] Ptilde)) = red(h([v] Ptilde))
    iff x([u]P) = x([v]P)
    iff u = +v or -v (mod r).
```

Thus the full orbit indexed by `(Z/rZ)^* / {+1,-1}` has exactly `(r-1)/2` distinct reduced Weber values, all in the residue field when the prime splits completely. Splitting makes Frobenius fix each value; it does not identify the values with each other. For exceptional `j = 0` or `1728`, replace the sign quotient by the full automorphism quotient and use the corresponding Weber function. [pcc:unverified]

The same distinction applies to a degree-`ell` quotient of the ray class extension. Trivial Frobenius on that quotient does not imply that an invariant distinguishing its Galois conjugates becomes constant after reduction. A *particular* chosen polynomial generator may suffer accidental modular collisions; that requires a separate discriminant or direct-value check. Neither complete splitting nor `pi = 1 mod n` proves the universal constant-value prediction in the proposed record. [pcc:unverified]

## Exact finite-field control

The following self-contained Sage calculation uses the checked local launcher. It does not construct the characteristic-zero ray class field; it checks the finite-field distinctness forced by injective reduction and the proposal's claimed orbit action. [pcc:unverified]

```sh
/Volumes/SSD990/cryptanalysis/sage -python - <<'PY'
from sage.all import GF, EllipticCurve, ZZ, QuadraticField
p, r = 47, 61
E = EllipticCurve(GF(p), [1, 38])
G = E(2, 1)
t = p + 1 - r
D = t*t - 4*p
xs = {int((k*G)[0]) for k in range(1, r)}
assert E.cardinality() == r and (r*G).is_zero()
assert D == -19 and ZZ(D).is_fundamental_discriminant()
assert QuadraticField(D).class_number() == 1
assert len(xs) == (r-1)//2
print({'p':p, 'r':r, 'D':D, 'x_orbit_size':len(xs),
       'x_G':int(G[0]), 'x_2G':int((2*G)[0])})
PY
```

Observed output: `{'p': 47, 'r': 61, 'D': -19, 'x_orbit_size': 30, 'x_G': 2, 'x_2G': 3}`. The trace is `-13`, so `D = (-13)^2 - 4*47 = -19`; since this is fundamental, the endomorphism order is maximal. Here `j(E)=39`, distinct from `0` and `1728 mod 47`. The ray modulus `(pi-1)` has norm `61`, and `pi = 1 mod (pi-1)` still holds. The 30 distinct reduced x-values directly contradict the proposed one-value prediction for the generic Weber orbit. [pcc:unverified]

P-192 also has fundamental Frobenius discriminant `-24109379060336110122544161233113975664949272517896865359515`, and its standard generator has different x-coordinates from its double. This is a second elementary check of distinctness, not a construction of the enormous ray class field. [pcc:unverified]

## What remains open

The reduced values are distinct, but their field coordinates do not come with computable ray-class labels. Given `Q=[d]G`, locating `x(Q)` in a fully labelled list `u -> x([u]G)` is the original point-log problem in another representation; materializing the list costs `Theta(r)`. A useful bridge would compute a nonconstant, efficiently evaluable function of `x(Q)` whose value identifies a quotient of the ray label, with a complete construction cost and a matched known-scalar control. The trivial Artin symbol does not rule out such a function, and injective reduction does not supply it. [pcc:unverified]
