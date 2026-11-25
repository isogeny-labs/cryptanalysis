# Elliptic Gauss sums and the missing target orientation

## Prior-art match

The character-weighted sum in [the ray-label character gate](RAY_LABEL_CHARACTER_GATE.md) is a Lagrange resolvent of torsion coordinates. [Berghoff, *Efficient computation of universal elliptic Gauß sums* (2017)](https://arxiv.org/abs/1707.08610) studies closely related elliptic Gauss sums for point counting. Its equations (1.2)–(1.4) use a character on `F_ell^*` and an `ell`-torsion eigenpoint to determine a **Frobenius eigenvalue** modulo `ell`; its theorem 2.1 constructs modular functions for powers of the sum. The paper chooses x or y coordinates according to the character's parity, so its displayed sum should not be identified term-for-term with our sign-invariant quadratic x-sum. The existing [auxiliary-torsion Fourier proposal](https://github.com/isogeny-labs/crypto-autoresearcher/blob/main/ledger/proposals/IDEA-20260906-91453a.yaml) is another nearby construction. Character resolvents themselves are established mathematics, and no novelty claim is made here. [pcc:unverified]

## Orientation is exactly the target-dependent part

For the quadratic x-resolvent `R` in the linked note, `R([d]G)=chi_r(d)R(G)`. Squaring removes the unknown sign:

```text
R([d]G)^2 = R(G)^2  for every nonzero d mod r.
```

Thus a curve-only formula for `R(G)^2` cannot distinguish `G` from `Q=[d]G`. In the exact `p=47, r=61, D=-19` control, `R(G)=17` and `R(2G)=30=-17 mod 47`, while both squares equal `7 mod 47`. The unknown scalar's quadratic character lives in the **choice of square root relative to G**, which is the orientation that the invariant power discards. A formula depending only on `j(E)`, a horizontal ideal class, or another curve-only value also cannot recover that sign. [pcc:unverified]

Berghoff's universal method targets the invariant `n`-th power of a character sum, which is sufficient for its small-`ell` Frobenius-eigenvalue task. Its equation (3.7) gives cost `O(M(n)((v+e_Delta+1)ell + log p))` in its stated parameters, after the required modular-function data are available. Setting `ell=r` on a prime-order ECDLP instance is outside the small-prime point-counting regime and retains an `ell` term; the published bound does not supply a sub-rho evaluator for the target-dependent unsquared resolvent. On `E(F_p)[r]`, Frobenius acts as scalar `1`, so identifying its eigenvalue gives no information about `d`. These are scope and cost observations about this published construction, not a lower bound on all Gauss-sum algorithms. [pcc:unverified]

## Next construction gate

The useful missing primitive is an **oriented target evaluator**: from `(E,G,Q)`, compute a nontrivial quotient of `d` using the coordinates of `Q`, with setup, map evaluation, any modular-function precomputation, and full recovery charged. A candidate must pass two immediate controls before a large run:

1. On the `D=-19` instance, distinguish `G` from `2G` by the correct character sign while the curve-only square remains `7`.
2. On a matched generic cyclic curve, show an advantage attributable to the proposed CM construction rather than the generic resolvent identity or an uncharged character table.

The target evaluator must then be costed against the full same-target rho solve, not merely against direct evaluation of a `r/2`-term sum. Smooth principal ideals can permute the resolvent's terms and contribute known scalar character factors; this alone leaves the target orientation to be computed. [pcc:unverified]
