# T-1805 blind algebra and nearby false controls

## Polynomial identity

Put `t = X³`. Direct expansion over the integers gives

```text
(t − 16)(t + 128)² = t³ + 240t² + 12288t − 262144,
(t − 64)³         = t³ − 192t² + 12288t − 262144.
```

Their difference is `432t² = 432X⁶`. This is an identity in `ℤ[X]`, so substitution proves it for every element of every commutative ring, including rings of positive characteristic and `X = 0`.

## On-curve identity

Let `K` be a field, `X ∈ K` with `X ≠ 0`, and `Y² = X³ − 16`. Set

```text
U = (X³ − 64)/X²,       V = Y(X³ + 128)/X³.
```

Since `X⁶` is invertible,

```text
V² − U³ − 432
  = [Y²(X³ + 128)² − (X³ − 64)³ − 432X⁶]/X⁶
  = [(X³ − 16)(X³ + 128)² − (X³ − 64)³ − 432X⁶]/X⁶
  = 0.
```

Thus the displayed rational formulas send every source-curve affine point in their domain `X ≠ 0` to a point satisfying `V² = U³ + 432`.

## Nearby false controls and boundary

**Change 128 to 127.** With `t = X³`, the altered polynomial difference is

```text
(t − 16)(t + 127)² − (t − 64)³
  = 430t² − 223t + 4080
  = 432t² + (−2t² − 223t + 4080).
```

For the real source point `X = 3`, `Y = √11`, the altered output has

```text
V₁₂₇² = 11·154²/729 = 260876/729,
U³ + 432 = (−37/9)³ + 432 = 264275/729.
```

Their difference is `−3399/729 = −1133/243 ≠ 0`. The 127 formula is therefore not a general on-curve identity. In some fields or at some points the error polynomial can vanish; the counterexample rules out the universal assertion.

**Drop the source equation.** For arbitrary `Y` and nonzero `X`, the exact defect is

```text
V² − U³ − 432
  = [Y² − (X³ − 16)](X³ + 128)²/X⁶.
```

For example, over `ℚ`, take `X = 1`, `Y = 0`. Then `V² = 0` while `U³ + 432 = (−63)³ + 432 = −249615`. The on-curve assertion fails. The factorization also shows that the source equation is sufficient, and that it is not logically necessary at exceptional points where `X³ + 128 = 0`.

**Set `X = 0`.** The polynomial identity reads `−16·128² − (−64)³ = 0`. The rational formulas for `U` and `V` contain division by `X²` and `X³`, so they do not define outputs at `X = 0`. The source equation there is `Y² = −16`, whose solvability depends on the field. No value or extension of the rational map at that point follows from these equations.

## Claim scope and verdict

The equations establish an integral polynomial identity and on-curve preservation by the displayed rational formulas on `X ≠ 0`. They alone do not establish an extension at `X = 0`, a group homomorphism, an isogeny, its degree, or a dual-map relation. The requested blind algebra and nearby false controls **hold** with the domain and source-equation hypotheses stated above.
