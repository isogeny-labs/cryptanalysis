# Formal verification receipt: concrete plane-cubic good-reduction chord bridge

Date: 2026-11-18

Pinned Lean `leanprover/lean4:v4.35.0-rc4` and Mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9` built
`GoodReductionChordBridge.lean` with zero errors and audited all 16 named
theorems (30 module constants including structure equations) with zero failing
and zero compiler-trust foundations. [pcc:unverified]

Every theorem uses only standard Lean foundations (`propext`,
`Classical.choice`, and `Quot.sound` as applicable), with no `sorry`, `admit`,
`sorryAx`, `native_decide`, or project-defined assumptions. [pcc:unverified]

## Proof map

| Lean theorem (`XedniChordBridge.*`) | Mathematical statement | Foundations |
|---|---|---|
| `binaryRestriction_spec` | Exact expansion `evalCubic c (s • P + t • Q) = b0 s^3 + b1 s^2 t + b2 s t^2 + b3 t^3` in JKSST monomial order | `propext` |
| `chordRaw_on_cubic` | For `evalCubic c P = 0` and `evalCubic c Q = 0`, `evalCubic c (chordRaw c P Q) = 0` over any `CommRing` | `propext, Quot.sound` |
| `tangentRaw_on_cubic` | For `evalCubic c P = 0` and double contact `b1 c P aux = 0`, `evalCubic c (tangentRaw c P aux) = 0` | `propext, Quot.sound` |
| `chordRaw_map` | Good-reduction functoriality `φ ∘ chordRaw c P Q = chordRaw (mapCubic φ c) (φ ∘ P) (φ ∘ Q)` for `φ : R →+* S` | `propext, Classical.choice, Quot.sound` |
| `chordRaw_smul_cubic_and_points` | Homogeneous scaling `chordRaw (μ • c) (u • P) (v • Q) = (μ * u^2 * v^2) • chordRaw c P Q` | `propext, Quot.sound` |
| `chordRaw_linear_equivariant` | `GL_3` linear pullback equivariance `chordRaw c' (L P) (L Q) = μ • L (chordRaw c P Q)` | `propext, Classical.choice, Quot.sound` |
| `chordRaw_mulVec_equivariant` | Characteristic-free `Matrix (Fin 3) (Fin 3) R` equivariance under `b1, b2` invariance | `propext, Classical.choice, Quot.sound` |
| `primitive_reduction_noncollapse` | If `V = g • O` in `Fin 3 → ℤ` and `φ ∘ V ≠ 0` over a field `F`, then `φ g ≠ 0` (`p ∤ g`), `φ ∘ O ≠ 0`, and `φ ∘ V = φ g • (φ ∘ O)` | `propext, Quot.sound` |
| `weierstrass_chordRaw_of_X_ne` | On `weierstrassPlaneCubic W` with `x₁ ≠ x₂`, `chordRaw = (x₁ - x₂)^3 • ![addX, negAddY, 1]` | `propext, Classical.choice, Quot.sound` |
| `weierstrass_chordRaw_of_X_eq` | On `weierstrassPlaneCubic W` with `x₁ = x₂`, `chordRaw = (y₁ - y₂)^3 • ![0, 1, 0]` | `propext, Classical.choice, Quot.sound` |
| `weierstrass_chordRaw_ne_zero` | Distinct affine points on `W` never collapse `chordRaw` to `(0, 0, 0)` | `propext, Classical.choice, Quot.sound` |
| `weierstrass_toAffine_chordRaw` | Mathlib's `Projective.Point.toAffine` maps `chordRaw` on `W` to `-(P₁ + P₂)` in `W.toAffine.Point` | `propext, Classical.choice, Quot.sound` |
| `good_reduction_chord_origin_scalar` | Concrete bridge: for any integer cubic `c` reducing to `μ • weierstrassPlaneCubic W` (`μ ≠ 0`), projective lifts `P, Q` of distinct nonsingular `m_j • G, m_k • G`, and primitive `chordRaw c P Q = g • O`, automatically `φ g ≠ 0`, `φ ∘ O ≠ 0`, and `toAffine W (φ ∘ O) = -(m_j + m_k) • G` | `propext, Classical.choice, Quot.sound` |
| `good_reduction_shifted_relation` | End-to-end scalar bridge: any reduced shifted relation `∑_i n_i • (m_i • G - toAffine W (φ ∘ O)) = 0` implies `(∑_i n_i * (m_i + m_j + m_k)) • G = 0` in `W.toAffine.Point` | `propext, Classical.choice, Quot.sound` |
| `origin_local_iff_fixed_transport` | In any `AddCommGroup`, origin-local exactness relative to `O = -(P_u + P_v)` is equivalent to fixed-flex exactness of `r = n + S e_u + S e_v` | `propext, Classical.choice, Quot.sound` |
| `collinear_triple_shifted_relation` | Any collinear triple `P_a + P_b + P_c = 0` automatically satisfies the five-term shifted relation `(P_a - O) + (P_b - O) + (P_c - O) - (P_u - O) - (P_v - O) = 0` | `propext` |

## Scope boundary

This module closes the concrete good-reduction chord-origin bridge from the
ten-coefficient plane-cubic chord formula and its primitive integer
representative to Mathlib's `WeierstrassCurve.Affine.Point` group law, as well
as homogeneous/projective frame scaling and translated-origin divisor
transport. [pcc:unverified]

What remains external to Lean is a full scheme-theoretic Picard-group
formalization proving that the arbitrary-origin two-chord addition law on a
general smooth plane cubic over `ℚ` defines a group homomorphism under good
reduction at `p` for multi-step scalar multiplications (`relation_sum`); the
executable code checks every candidate relation both over `ℚ` and directly in
`E(𝔽_p)`. [pcc:unverified]

## Reproduce

```sh
cd experiments/xedni-chord-origin-bridge-20261118/formal
lake exe cache get
lake build GoodReductionChordBridge
```
