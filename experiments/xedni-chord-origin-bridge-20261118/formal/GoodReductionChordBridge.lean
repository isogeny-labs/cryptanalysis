import Mathlib.AlgebraicGeometry.EllipticCurve.Projective.Point

namespace XedniChordBridge

open WeierstrassCurve

/-- Homogeneous plane cubic in JKSST monomial order
`(X^3, X^2 Y, X Y^2, Y^3, X^2 Z, X Y Z, Y^2 Z, X Z^2, Y Z^2, Z^3)`,
matching `PLANE_CUBIC_COEFFICIENTS` in `suite/src/cryptanalysis/xedni_lift.rs`. -/
@[ext]
structure PlaneCubic (R : Type*) where
  c0 : R
  c1 : R
  c2 : R
  c3 : R
  c4 : R
  c5 : R
  c6 : R
  c7 : R
  c8 : R
  c9 : R

instance {R : Type*} [Mul R] : SMul R (PlaneCubic R) where
  smul μ c :=
    ⟨μ * c.c0, μ * c.c1, μ * c.c2, μ * c.c3, μ * c.c4,
     μ * c.c5, μ * c.c6, μ * c.c7, μ * c.c8, μ * c.c9⟩

/-- Map plane-cubic coefficients along a ring homomorphism (for example reduction modulo `p`). -/
def mapCubic {R S : Type*} [CommRing R] [CommRing S] (φ : R →+* S) (c : PlaneCubic R) :
    PlaneCubic S :=
  ⟨φ c.c0, φ c.c1, φ c.c2, φ c.c3, φ c.c4, φ c.c5, φ c.c6, φ c.c7, φ c.c8, φ c.c9⟩

/-- Evaluate a ten-coefficient ternary cubic at a projective triple `P : Fin 3 → R`. -/
def evalCubic {R : Type*} [CommRing R] (c : PlaneCubic R) (P : Fin 3 → R) : R :=
  let X := P 0
  let Y := P 1
  let Z := P 2
  c.c0 * X ^ 3 + c.c1 * X ^ 2 * Y + c.c2 * X * Y ^ 2 + c.c3 * Y ^ 3 +
    c.c4 * X ^ 2 * Z + c.c5 * X * Y * Z + c.c6 * Y ^ 2 * Z +
    c.c7 * X * Z ^ 2 + c.c8 * Y * Z ^ 2 + c.c9 * Z ^ 3

/-- Coefficient of `s^3` in `evalCubic c (s • P + t • Q)`. -/
def b0 {R : Type*} [CommRing R] (c : PlaneCubic R) (P _Q : Fin 3 → R) : R :=
  evalCubic c P

/-- Coefficient of `s^2 t` in `evalCubic c (s • P + t • Q)`, matching
`binary_cubic_restriction[1]` in `xedni_lift.rs`. -/
def b1 {R : Type*} [CommRing R] (c : PlaneCubic R) (P Q : Fin 3 → R) : R :=
  let px := P 0; let py := P 1; let pz := P 2
  let qx := Q 0; let qy := Q 1; let qz := Q 2
  c.c0 * (3 * px ^ 2 * qx) +
    c.c1 * (2 * px * qx * py + px ^ 2 * qy) +
    c.c2 * (qx * py ^ 2 + 2 * px * py * qy) +
    c.c3 * (3 * py ^ 2 * qy) +
    c.c4 * (2 * px * qx * pz + px ^ 2 * qz) +
    c.c5 * (qx * py * pz + px * qy * pz + px * py * qz) +
    c.c6 * (2 * py * qy * pz + py ^ 2 * qz) +
    c.c7 * (qx * pz ^ 2 + 2 * px * pz * qz) +
    c.c8 * (qy * pz ^ 2 + 2 * py * pz * qz) +
    c.c9 * (3 * pz ^ 2 * qz)

/-- Coefficient of `s t^2` in `evalCubic c (s • P + t • Q)`, matching
`binary_cubic_restriction[2]` in `xedni_lift.rs`. -/
def b2 {R : Type*} [CommRing R] (c : PlaneCubic R) (P Q : Fin 3 → R) : R :=
  b1 c Q P

/-- Coefficient of `t^3` in `evalCubic c (s • P + t • Q)`. -/
def b3 {R : Type*} [CommRing R] (c : PlaneCubic R) (_P Q : Fin 3 → R) : R :=
  evalCubic c Q

/-- Unnormalized chord residual `b₂ • P - b₁ • Q`, matching
`combine_projective(&restriction[2], p, &-restriction[1], q)` in
`PlaneCubicGroup::third_intersection` (`xedni_lift.rs`). -/
def chordRaw {R : Type*} [CommRing R] (c : PlaneCubic R) (P Q : Fin 3 → R) : Fin 3 → R :=
  b2 c P Q • P - b1 c P Q • Q

/-- Unnormalized tangent residual `b₃ • P - b₂ • aux` for double contact (`b₀ = b₁ = 0`),
matching the tangent branch of `PlaneCubicGroup::third_intersection`. -/
def tangentRaw {R : Type*} [CommRing R] (c : PlaneCubic R) (P aux : Fin 3 → R) : Fin 3 → R :=
  b3 c P aux • P - b2 c P aux • aux

/-- Embed a general Mathlib `WeierstrassCurve R`
(`Y^2 Z + a₁ X Y Z + a₃ Y Z^2 = X^3 + a₂ X^2 Z + a₄ X Z^2 + a₆ Z^3`)
as the ten-coefficient plane cubic
`X^3 + a₂ X^2 Z - a₁ X Y Z - Y^2 Z + a₄ X Z^2 - a₃ Y Z^2 + a₆ Z^3`.
For short Weierstrass `(0, 0, 0, a, b)` this equals `[1, 0, 0, 0, 0, 0, -1, a, 0, b]`. -/
def weierstrassPlaneCubic {R : Type*} [CommRing R] (W : WeierstrassCurve R) : PlaneCubic R :=
  ⟨1, 0, 0, 0, W.a₂, -W.a₁, -1, W.a₄, -W.a₃, W.a₆⟩

/-- Restricting any ternary cubic `c` to the line `s • P + t • Q` expands into the exact binary cubic
`(b0, b1, b2, b3)`. -/
theorem binaryRestriction_spec {R : Type*} [CommRing R]
    (c : PlaneCubic R) (P Q : Fin 3 → R) (s t : R) :
    evalCubic c (s • P + t • Q) =
      b0 c P Q * s ^ 3 + b1 c P Q * s ^ 2 * t + b2 c P Q * s * t ^ 2 + b3 c P Q * t ^ 3 := by
  simp only [evalCubic, b0, b1, b2, b3, Pi.add_apply, Pi.smul_apply, smul_eq_mul]
  ring

/-- When `P` and `Q` lie on `c`, the unnormalized chord residual `chordRaw c P Q` lies on `c`
over every commutative ring. -/
theorem chordRaw_on_cubic {R : Type*} [CommRing R]
    (c : PlaneCubic R) (P Q : Fin 3 → R) (hP : evalCubic c P = 0) (hQ : evalCubic c Q = 0) :
    evalCubic c (chordRaw c P Q) = 0 := by
  have hsub : chordRaw c P Q = b2 c P Q • P + (-b1 c P Q) • Q := by
    ext i
    simp [chordRaw, sub_eq_add_neg]
  rw [hsub, binaryRestriction_spec]
  simp only [b0, b3, hP, hQ]
  ring

/-- When `P` has double contact along `P, aux` (`evalCubic c P = 0` and `b1 c P aux = 0`),
the tangent residual `tangentRaw c P aux` lies on `c`. -/
theorem tangentRaw_on_cubic {R : Type*} [CommRing R]
    (c : PlaneCubic R) (P aux : Fin 3 → R)
    (hP : evalCubic c P = 0) (htan : b1 c P aux = 0) :
    evalCubic c (tangentRaw c P aux) = 0 := by
  have hsub : tangentRaw c P aux = b3 c P aux • P + (-b2 c P aux) • aux := by
    ext i
    simp [tangentRaw, sub_eq_add_neg]
  rw [hsub, binaryRestriction_spec]
  simp only [b0, hP, htan]
  ring

/-- `chordRaw` commutes with every ring homomorphism `φ : R →+* S` (good reduction). -/
theorem chordRaw_map {R S : Type*} [CommRing R] [CommRing S]
    (φ : R →+* S) (c : PlaneCubic R) (P Q : Fin 3 → R) :
    φ ∘ chordRaw c P Q = chordRaw (mapCubic φ c) (φ ∘ P) (φ ∘ Q) := by
  ext i
  simp only [Function.comp_apply, chordRaw, mapCubic, b2, b1,
    Pi.sub_apply, Pi.smul_apply, smul_eq_mul, map_sub, map_mul, map_add, map_pow, map_ofNat]

/-- Homogeneous rescaling of the cubic by `μ` and projective point representatives by `u, v`
scales `chordRaw` by `μ * u^2 * v^2`. -/
theorem chordRaw_smul_cubic_and_points {R : Type*} [CommRing R]
    (μ u v : R) (c : PlaneCubic R) (P Q : Fin 3 → R) :
    chordRaw (μ • c) (u • P) (v • Q) = (μ * u ^ 2 * v ^ 2) • chordRaw c P Q := by
  ext i
  change
    b2 ⟨μ * c.c0, μ * c.c1, μ * c.c2, μ * c.c3, μ * c.c4,
        μ * c.c5, μ * c.c6, μ * c.c7, μ * c.c8, μ * c.c9⟩ (u • P) (v • Q) * (u * P i) -
      b1 ⟨μ * c.c0, μ * c.c1, μ * c.c2, μ * c.c3, μ * c.c4,
          μ * c.c5, μ * c.c6, μ * c.c7, μ * c.c8, μ * c.c9⟩ (u • P) (v • Q) * (v * Q i) =
    (μ * u ^ 2 * v ^ 2) * (b2 c P Q * P i - b1 c P Q * Q i)
  simp only [b2, b1, Pi.smul_apply, smul_eq_mul]
  ring

/-- `GL_3` projective-frame equivariance: if a linear map `L : (Fin 3 → R) →ₗ[R] (Fin 3 → R)` pulls back
`c'` to `μ * evalCubic c` (as in JKSST four-point frame normalization), then `chordRaw` is `L`-equivariant
up to the homogeneous scalar `μ`. -/
theorem chordRaw_linear_equivariant {R : Type*} [CommRing R]
    [NoZeroSMulDivisors ℤ R]
    (L : (Fin 3 → R) →ₗ[R] (Fin 3 → R)) (c c' : PlaneCubic R) (μ : R)
    (hpull : ∀ v : Fin 3 → R, evalCubic c' (L v) = μ * evalCubic c v)
    (P Q : Fin 3 → R) :
    chordRaw c' (L P) (L Q) = μ • L (chordRaw c P Q) := by
  have hpoly : ∀ s t : R,
      b0 c' (L P) (L Q) * s ^ 3 + b1 c' (L P) (L Q) * s ^ 2 * t +
          b2 c' (L P) (L Q) * s * t ^ 2 + b3 c' (L P) (L Q) * t ^ 3 =
        μ * (b0 c P Q * s ^ 3 + b1 c P Q * s ^ 2 * t + b2 c P Q * s * t ^ 2 + b3 c P Q * t ^ 3) := by
    intro s t
    rw [← binaryRestriction_spec c' (L P) (L Q) s t, ← L.map_smul s P, ← L.map_smul t Q,
      ← L.map_add, hpull, binaryRestriction_spec c P Q s t]
  have h10 := hpoly 1 0
  have h01 := hpoly 0 1
  have h11 := hpoly 1 1
  have h1m1 := hpoly 1 (-1)
  have hb0 : b0 c' (L P) (L Q) = μ * b0 c P Q := by linear_combination h10
  have hb3 : b3 c' (L P) (L Q) = μ * b3 c P Q := by linear_combination h01
  have hsum : b1 c' (L P) (L Q) + b2 c' (L P) (L Q) = μ * (b1 c P Q + b2 c P Q) := by
    linear_combination h11 - hb0 - hb3
  have hdiff : b2 c' (L P) (L Q) - b1 c' (L P) (L Q) = μ * (b2 c P Q - b1 c P Q) := by
    linear_combination h1m1 - hb0 + hb3
  have h2b1 : (2 : ℤ) • (b1 c' (L P) (L Q) - μ * b1 c P Q) = 0 := by
    simp only [zsmul_eq_mul, Int.cast_ofNat]
    linear_combination hsum - hdiff
  have hb1 : b1 c' (L P) (L Q) = μ * b1 c P Q :=
    sub_eq_zero.mp ((smul_eq_zero.mp h2b1).resolve_left (by decide))
  have hb2 : b2 c' (L P) (L Q) = μ * b2 c P Q := by
    linear_combination hsum - hb1
  ext i
  simp only [chordRaw, hb1, hb2, LinearMap.map_sub, LinearMap.map_smul,
    Pi.sub_apply, Pi.smul_apply, smul_eq_mul]
  ring

/-- Characteristic-free `GL_3` matrix equivariance over every commutative ring (including finite fields
of arbitrary characteristic), whenever `c'` pulls back the binary restriction coefficients `b₁, b₂`. -/
theorem chordRaw_mulVec_equivariant {R : Type*} [CommRing R]
    (M : Matrix (Fin 3) (Fin 3) R) (c c' : PlaneCubic R) (P Q : Fin 3 → R)
    (hb1 : b1 c' (M.mulVec P) (M.mulVec Q) = b1 c P Q)
    (hb2 : b2 c' (M.mulVec P) (M.mulVec Q) = b2 c P Q) :
    chordRaw c' (M.mulVec P) (M.mulVec Q) = M.mulVec (chordRaw c P Q) := by
  rw [chordRaw, hb1, hb2, chordRaw, Matrix.mulVec_sub, Matrix.mulVec_smul, Matrix.mulVec_smul]

/-- Automatic non-collapse of primitive integer normalization (`PlaneCubicPoint::new`):
if `V = g • O` in `Fin 3 → ℤ` and the reduced vector `φ ∘ V` in `Fin 3 → F` is nonzero,
then `φ g ≠ 0` in `F` (so `p ∤ g`), `φ ∘ O ≠ 0`, and `φ ∘ V = φ g • (φ ∘ O)`. -/
theorem primitive_reduction_noncollapse {F : Type*} [Field F]
    (φ : ℤ →+* F) (V O : Fin 3 → ℤ) (g : ℤ)
    (hprim : V = g • O) (hV : φ ∘ V ≠ 0) :
    φ g ≠ 0 ∧ φ ∘ O ≠ 0 ∧ φ ∘ V = φ g • (φ ∘ O) := by
  have hrel : φ ∘ V = φ g • (φ ∘ O) := by
    ext i
    simp [hprim, Function.comp_apply, Pi.smul_apply, zsmul_eq_mul]
  refine ⟨?_, ?_, hrel⟩
  · intro hg
    apply hV
    rw [hrel, hg, zero_smul]
  · intro hO
    apply hV
    rw [hrel, hO, smul_zero]

/-- On `weierstrassPlaneCubic W`, two affine points `(x₁, y₁, 1)` and `(x₂, y₂, 1)` with `x₁ ≠ x₂`
have exact chord residual `(x₁ - x₂)^3 • ![addX, negAddY, 1]`. -/
theorem weierstrass_chordRaw_of_X_ne {F : Type*} [Field F] [DecidableEq F]
    (W : WeierstrassCurve F) {x₁ y₁ x₂ y₂ : F}
    (h₁ : W.toAffine.Equation x₁ y₁) (h₂ : W.toAffine.Equation x₂ y₂) (hx : x₁ ≠ x₂) :
    chordRaw (weierstrassPlaneCubic W) ![x₁, y₁, 1] ![x₂, y₂, 1] =
      (x₁ - x₂) ^ 3 •
        ![W.toAffine.addX x₁ x₂ (W.toAffine.slope x₁ x₂ y₁ y₂),
          W.toAffine.negAddY x₁ x₂ y₁ (W.toAffine.slope x₁ x₂ y₁ y₂),
          1] := by
  have hsub : x₁ - x₂ ≠ 0 := sub_ne_zero.mpr hx
  have heq₁ : y₁ ^ 2 + W.a₁ * x₁ * y₁ + W.a₃ * y₁ =
      x₁ ^ 3 + W.a₂ * x₁ ^ 2 + W.a₄ * x₁ + W.a₆ := (WeierstrassCurve.Affine.equation_iff ..).mp h₁
  have heq₂ : y₂ ^ 2 + W.a₁ * x₂ * y₂ + W.a₃ * y₂ =
      x₂ ^ 3 + W.a₂ * x₂ ^ 2 + W.a₄ * x₂ + W.a₆ := (WeierstrassCurve.Affine.equation_iff ..).mp h₂
  rw [WeierstrassCurve.Affine.slope_of_X_ne hx]
  rw [funext_iff, Fin.forall_fin_succ, Fin.forall_fin_succ, Fin.forall_fin_one]
  refine ⟨?_, ?_, ?_⟩
  · simp only [Fin.isValue,
      chordRaw, weierstrassPlaneCubic, b2, b1, WeierstrassCurve.Affine.addX,
      Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_two, Matrix.tail_cons, Matrix.head_cons,
      Pi.sub_apply, Pi.smul_apply, smul_eq_mul]
    field_simp [hsub]
    linear_combination (-x₁ + 2 * x₂) * heq₁ + (-2 * x₁ + x₂) * heq₂
  · simp only [Fin.isValue, Fin.succ_zero_eq_one,
      chordRaw, weierstrassPlaneCubic, b2, b1,
      WeierstrassCurve.Affine.negAddY, WeierstrassCurve.Affine.addX,
      Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_two, Matrix.tail_cons, Matrix.head_cons,
      Pi.sub_apply, Pi.smul_apply, smul_eq_mul]
    field_simp [hsub]
    linear_combination (-y₁ + 2 * y₂) * heq₁ + (-2 * y₁ + y₂) * heq₂
  · simp only [Fin.isValue, Fin.succ_zero_eq_one, Fin.succ_one_eq_two,
      chordRaw, weierstrassPlaneCubic, b2, b1,
      Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_two, Matrix.tail_cons, Matrix.head_cons,
      Pi.sub_apply, Pi.smul_apply, smul_eq_mul]
    linear_combination heq₁ - heq₂

/-- On `weierstrassPlaneCubic W`, two affine points `(x₁, y₁, 1)` and `(x₁, y₂, 1)` on the same
vertical line have exact chord residual `(y₁ - y₂)^3 • ![0, 1, 0]` (a multiple of the flex `𝓞`). -/
theorem weierstrass_chordRaw_of_X_eq {F : Type*} [Field F]
    (W : WeierstrassCurve F) {x₁ y₁ x₂ y₂ : F}
    (h₁ : W.toAffine.Equation x₁ y₁) (h₂ : W.toAffine.Equation x₂ y₂) (hx : x₁ = x₂) :
    chordRaw (weierstrassPlaneCubic W) ![x₁, y₁, 1] ![x₂, y₂, 1] =
      (y₁ - y₂) ^ 3 • ![0, 1, 0] := by
  subst hx
  have heq₁ : y₁ ^ 2 + W.a₁ * x₁ * y₁ + W.a₃ * y₁ =
      x₁ ^ 3 + W.a₂ * x₁ ^ 2 + W.a₄ * x₁ + W.a₆ := (WeierstrassCurve.Affine.equation_iff ..).mp h₁
  have heq₂ : y₂ ^ 2 + W.a₁ * x₁ * y₂ + W.a₃ * y₂ =
      x₁ ^ 3 + W.a₂ * x₁ ^ 2 + W.a₄ * x₁ + W.a₆ := (WeierstrassCurve.Affine.equation_iff ..).mp h₂
  have hy_rel : y₁ ^ 2 + W.a₁ * x₁ * y₁ + W.a₃ * y₁ = y₂ ^ 2 + W.a₁ * x₁ * y₂ + W.a₃ * y₂ := by
    linear_combination heq₁ - heq₂
  rw [funext_iff, Fin.forall_fin_succ, Fin.forall_fin_succ, Fin.forall_fin_one]
  refine ⟨?_, ?_, ?_⟩
  · simp only [Fin.isValue,
      chordRaw, weierstrassPlaneCubic, b2, b1,
      Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_two, Matrix.tail_cons, Matrix.head_cons,
      Pi.sub_apply, Pi.smul_apply, smul_eq_mul]
    linear_combination x₁ * hy_rel
  · simp only [Fin.isValue, Fin.succ_zero_eq_one,
      chordRaw, weierstrassPlaneCubic, b2, b1,
      Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_two, Matrix.tail_cons, Matrix.head_cons,
      Pi.sub_apply, Pi.smul_apply, smul_eq_mul]
    linear_combination (-y₁ + 2 * y₂) * heq₁ + (-2 * y₁ + y₂) * heq₂
  · simp only [Fin.isValue, Fin.succ_zero_eq_one, Fin.succ_one_eq_two,
      chordRaw, weierstrassPlaneCubic, b2, b1,
      Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_two, Matrix.tail_cons, Matrix.head_cons,
      Pi.sub_apply, Pi.smul_apply, smul_eq_mul]
    linear_combination heq₁ - heq₂

/-- For any two distinct affine points on `W`, `chordRaw` on `weierstrassPlaneCubic W` is never `(0, 0, 0)`. -/
theorem weierstrass_chordRaw_ne_zero {F : Type*} [Field F] [DecidableEq F]
    (W : WeierstrassCurve F) {x₁ y₁ x₂ y₂ : F}
    (h₁ : W.toAffine.Equation x₁ y₁) (h₂ : W.toAffine.Equation x₂ y₂)
    (hne : (x₁, y₁) ≠ (x₂, y₂)) :
    chordRaw (weierstrassPlaneCubic W) ![x₁, y₁, 1] ![x₂, y₂, 1] ≠ 0 := by
  by_cases hx : x₁ = x₂
  · have hy : y₁ ≠ y₂ := fun hy => hne (Prod.ext hx hy)
    rw [weierstrass_chordRaw_of_X_eq W h₁ h₂ hx]
    intro hzero
    have h1 : ((y₁ - y₂) ^ 3 • (![0, 1, 0] : Fin 3 → F)) 1 = (0 : Fin 3 → F) 1 :=
      congr_fun hzero 1
    change (y₁ - y₂) ^ 3 * 1 = 0 at h1
    rw [mul_one] at h1
    exact pow_ne_zero 3 (sub_ne_zero.mpr hy) h1
  · rw [weierstrass_chordRaw_of_X_ne W h₁ h₂ hx]
    intro hzero
    have h2 := congr_fun hzero 2
    change (x₁ - x₂) ^ 3 * 1 = 0 at h2
    rw [mul_one] at h2
    exact pow_ne_zero 3 (sub_ne_zero.mpr hx) h2

/-- On `weierstrassPlaneCubic W`, Mathlib's `Projective.Point.toAffine` maps `chordRaw` of two distinct
nonsingular affine points `(x₁, y₁)` and `(x₂, y₂)` to `-(P₁ + P₂)` in `W.toAffine.Point`. -/
theorem weierstrass_toAffine_chordRaw {F : Type*} [Field F] [DecidableEq F]
    (W : WeierstrassCurve F) {x₁ y₁ x₂ y₂ : F}
    (h₁ : W.toAffine.Nonsingular x₁ y₁) (h₂ : W.toAffine.Nonsingular x₂ y₂)
    (hne : (x₁, y₁) ≠ (x₂, y₂)) :
    Projective.Point.toAffine W.toProjective
        (chordRaw (weierstrassPlaneCubic W) ![x₁, y₁, 1] ![x₂, y₂, 1]) =
      -(Affine.Point.some x₁ y₁ h₁ + Affine.Point.some x₂ y₂ h₂) := by
  by_cases hx : x₁ = x₂
  · have hy : y₁ ≠ y₂ := fun hy => hne (Prod.ext hx hy)
    have hneg : y₁ = W.toAffine.negY x₂ y₂ :=
      (WeierstrassCurve.Affine.Y_eq_of_X_eq h₁.1 h₂.1 hx).resolve_left hy
    rw [weierstrass_chordRaw_of_X_eq W h₁.1 h₂.1 hx,
      Projective.Point.toAffine_smul _ (Ne.isUnit (pow_ne_zero 3 (sub_ne_zero.mpr hy))),
      Projective.Point.toAffine_zero,
      Affine.Point.add_of_Y_eq hx hneg, neg_zero]
  · have hxy : ¬(x₁ = x₂ ∧ y₁ = W.toAffine.negY x₂ y₂) := fun h => hx h.1
    have hns_negAdd :
        W.toAffine.Nonsingular
          (W.toAffine.addX x₁ x₂ (W.toAffine.slope x₁ x₂ y₁ y₂))
          (W.toAffine.negAddY x₁ x₂ y₁ (W.toAffine.slope x₁ x₂ y₁ y₂)) :=
      WeierstrassCurve.Affine.nonsingular_negAdd h₁ h₂ hxy
    have hproj_ns :
        W.toProjective.Nonsingular
          ![W.toAffine.addX x₁ x₂ (W.toAffine.slope x₁ x₂ y₁ y₂),
            W.toAffine.negAddY x₁ x₂ y₁ (W.toAffine.slope x₁ x₂ y₁ y₂), 1] :=
      (Projective.nonsingular_some _ _).mpr hns_negAdd
    rw [weierstrass_chordRaw_of_X_ne W h₁.1 h₂.1 hx,
      Projective.Point.toAffine_smul _ (Ne.isUnit (pow_ne_zero 3 (sub_ne_zero.mpr hx))),
      Projective.Point.toAffine_some hproj_ns,
      Affine.Point.add_of_X_ne' hx, neg_neg]

/-- Concrete good-reduction geometric bridge for the Xedni chord origin:
if an integral plane cubic `c` reduces via `φ : ℤ →+* F` to `μ • weierstrassPlaneCubic W` (`μ ≠ 0`),
integral points `P, Q` reduce projectively to distinct nonsingular source multiples `m_j • G, m_k • G`,
and `O` is a primitive integral representative of `chordRaw c P Q` (`chordRaw c P Q = g • O`),
then `φ g ≠ 0`, `φ ∘ O ≠ 0`, and `O` reduces on `W` to `-(m_j + m_k) • G`. -/
theorem good_reduction_chord_origin_scalar {F : Type*} [Field F] [DecidableEq F]
    (φ : ℤ →+* F) (W : WeierstrassCurve F)
    (c : PlaneCubic ℤ) (P Q O : Fin 3 → ℤ) (g m_j m_k : ℤ)
    (G : W.toAffine.Point)
    {x₁ y₁ x₂ y₂ μ u₁ u₂ : F}
    (hμ : μ ≠ 0) (hu₁ : u₁ ≠ 0) (hu₂ : u₂ ≠ 0)
    (hc : mapCubic φ c = μ • weierstrassPlaneCubic W)
    (hP : φ ∘ P = u₁ • ![x₁, y₁, 1])
    (hQ : φ ∘ Q = u₂ • ![x₂, y₂, 1])
    (hprim : chordRaw c P Q = g • O)
    (hns₁ : W.toAffine.Nonsingular x₁ y₁)
    (hns₂ : W.toAffine.Nonsingular x₂ y₂)
    (hne : (x₁, y₁) ≠ (x₂, y₂))
    (hm₁ : Affine.Point.some x₁ y₁ hns₁ = m_j • G)
    (hm₂ : Affine.Point.some x₂ y₂ hns₂ = m_k • G) :
    φ g ≠ 0 ∧ φ ∘ O ≠ 0 ∧
      Projective.Point.toAffine W.toProjective (φ ∘ O) = -(m_j + m_k) • G := by
  have hscale_ne : μ * u₁ ^ 2 * u₂ ^ 2 ≠ 0 :=
    mul_ne_zero (mul_ne_zero hμ (pow_ne_zero 2 hu₁)) (pow_ne_zero 2 hu₂)
  have hV_eq :
      φ ∘ chordRaw c P Q =
        (μ * u₁ ^ 2 * u₂ ^ 2) •
          chordRaw (weierstrassPlaneCubic W) ![x₁, y₁, 1] ![x₂, y₂, 1] := by
    rw [chordRaw_map, hc, hP, hQ, chordRaw_smul_cubic_and_points]
  have hW_ne := weierstrass_chordRaw_ne_zero W hns₁.1 hns₂.1 hne
  have hV_ne : φ ∘ chordRaw c P Q ≠ 0 := by
    rw [hV_eq]
    intro hz
    exact hW_ne ((smul_eq_zero.mp hz).resolve_left hscale_ne)
  obtain ⟨hg_ne, hO_ne, hVO⟩ := primitive_reduction_noncollapse φ (chordRaw c P Q) O g hprim hV_ne
  refine ⟨hg_ne, hO_ne, ?_⟩
  have hO_eq :
      φ ∘ O =
        ((φ g)⁻¹ * (μ * u₁ ^ 2 * u₂ ^ 2)) •
          chordRaw (weierstrassPlaneCubic W) ![x₁, y₁, 1] ![x₂, y₂, 1] := by
    have h1 := congr_arg ((φ g)⁻¹ • ·) hVO
    simp only [smul_smul, inv_mul_cancel₀ hg_ne, one_smul] at h1
    rw [← h1, hV_eq, smul_smul]
  have hunit : IsUnit ((φ g)⁻¹ * (μ * u₁ ^ 2 * u₂ ^ 2)) :=
    Ne.isUnit (mul_ne_zero (inv_ne_zero hg_ne) hscale_ne)
  rw [hO_eq, Projective.Point.toAffine_smul _ hunit,
    weierstrass_toAffine_chordRaw W hns₁ hns₂ hne, hm₁, hm₂, ← add_zsmul, ← neg_zsmul]

/-- Composing the concrete good-reduction chord bridge with a reduced shifted group relation
`∑_i n_i • (m_i • G - O_red) = 0` yields the finite-field scalar equation
`(∑_i n_i * (m_i + m_j + m_k)) • G = 0` directly in `W.toAffine.Point`. -/
theorem good_reduction_shifted_relation {ι F : Type*} [Field F] [DecidableEq F]
    (s : Finset ι) (n m : ι → ℤ)
    (φ : ℤ →+* F) (W : WeierstrassCurve F)
    (c : PlaneCubic ℤ) (P Q O : Fin 3 → ℤ) (g m_j m_k : ℤ)
    (G : W.toAffine.Point)
    {x₁ y₁ x₂ y₂ μ u₁ u₂ : F}
    (hμ : μ ≠ 0) (hu₁ : u₁ ≠ 0) (hu₂ : u₂ ≠ 0)
    (hc : mapCubic φ c = μ • weierstrassPlaneCubic W)
    (hP : φ ∘ P = u₁ • ![x₁, y₁, 1])
    (hQ : φ ∘ Q = u₂ • ![x₂, y₂, 1])
    (hprim : chordRaw c P Q = g • O)
    (hns₁ : W.toAffine.Nonsingular x₁ y₁)
    (hns₂ : W.toAffine.Nonsingular x₂ y₂)
    (hne : (x₁, y₁) ≠ (x₂, y₂))
    (hm₁ : Affine.Point.some x₁ y₁ hns₁ = m_j • G)
    (hm₂ : Affine.Point.some x₂ y₂ hns₂ = m_k • G)
    (hrel :
      (∑ i ∈ s, n i • (m i • G - Projective.Point.toAffine W.toProjective (φ ∘ O))) = 0) :
    (∑ i ∈ s, n i * (m i + m_j + m_k)) • G = 0 := by
  obtain ⟨_, _, hO⟩ :=
    good_reduction_chord_origin_scalar φ W c P Q O g m_j m_k G
      hμ hu₁ hu₂ hc hP hQ hprim hns₁ hns₂ hne hm₁ hm₂
  rw [hO] at hrel
  have hsum :
      (∑ i ∈ s, n i • (m i • G - (-(m_j + m_k)) • G)) =
        (∑ i ∈ s, n i * (m i + m_j + m_k)) • G := by
    calc
      (∑ i ∈ s, n i • (m i • G - (-(m_j + m_k)) • G)) =
          ∑ i ∈ s, (n i * (m i + m_j + m_k)) • G := by
        apply Finset.sum_congr rfl
        intro i _
        simp only [mul_zsmul, neg_zsmul, sub_neg_eq_add, add_zsmul]
        abel_nf
      _ = (∑ i ∈ s, n i * (m i + m_j + m_k)) • G := by
        rw [← Finset.sum_smul]
  rwa [← hsum]

/-- Origin-transport equivalence in `Pic^0(C)` (closing the fixed-coordinate dedup bridge):
relative to any reference flex `0` where chord residual `O = -(P u + P v)`, an origin-local relation
`∑_i n_i • (P_i - O) = 0` is equivalent to `∑_i r_i • P_i = 0` for the transported fixed-flex key
`r_i = n_i + S δ_{i,u} + S δ_{i,v}` (`S = ∑_i n_i`). -/
theorem origin_local_iff_fixed_transport {ι A : Type*} [DecidableEq ι] [AddCommGroup A]
    (s : Finset ι) (n : ι → ℤ) (P : ι → A) {u v : ι} (hu : u ∈ s) (hv : v ∈ s) :
    let S := ∑ j ∈ s, n j
    let O := -(P u + P v)
    (∑ i ∈ s, n i • (P i - O) = 0) ↔
      (∑ i ∈ s, (n i + (if i = u then S else 0) + (if i = v then S else 0)) • P i = 0) := by
  intro S O
  have hleft :
      (∑ i ∈ s, n i • (P i - O)) =
        (∑ i ∈ s, n i • P i) + S • P u + S • P v := by
    simp only [O, sub_neg_eq_add, smul_add, Finset.sum_add_distrib, ← Finset.sum_smul, S, add_assoc]
  have hright :
      (∑ i ∈ s, (n i + (if i = u then S else 0) + (if i = v then S else 0)) • P i) =
        (∑ i ∈ s, n i • P i) + S • P u + S • P v := by
    simp only [add_zsmul, Finset.sum_add_distrib]
    have hu_sum : (∑ i ∈ s, (if i = u then S else 0) • P i) = S • P u := by
      rw [Finset.sum_eq_single u]
      · simp
      · intro i _ hne; simp [hne]
      · intro hnot; exact absurd hu hnot
    have hv_sum : (∑ i ∈ s, (if i = v then S else 0) • P i) = S • P v := by
      rw [Finset.sum_eq_single v]
      · simp
      · intro i _ hne; simp [hne]
      · intro hnot; exact absurd hv hnot
    rw [hu_sum, hv_sum]
  rw [hleft, hright]

/-- Curve-independent collinear-triple aliasing: if three lifted points satisfy `P_a + P_b + P_c = 0`
in `Pic^0(C)` (any hyperplane line section `P_a + P_b + P_c ~ H`), then for every chord origin
`O = -(P_u + P_v)`, the five-term shifted relation `(P_a - O) + (P_b - O) + (P_c - O) - (P_u - O) - (P_v - O) = 0`
holds automatically. -/
theorem collinear_triple_shifted_relation {A : Type*} [AddCommGroup A]
    (Pa Pb Pc Pu Pv : A) (hcol : Pa + Pb + Pc = 0) :
    let O := -(Pu + Pv)
    (Pa - O) + (Pb - O) + (Pc - O) - (Pu - O) - (Pv - O) = 0 := by
  intro O
  have h :
      (Pa - O) + (Pb - O) + (Pc - O) - (Pu - O) - (Pv - O) =
        (Pa + Pb + Pc) - (Pu + Pv + O) := by
    abel
  rw [h, hcol]
  simp [O]

#print axioms binaryRestriction_spec
#print axioms chordRaw_on_cubic
#print axioms tangentRaw_on_cubic
#print axioms chordRaw_map
#print axioms chordRaw_smul_cubic_and_points
#print axioms chordRaw_linear_equivariant
#print axioms chordRaw_mulVec_equivariant
#print axioms primitive_reduction_noncollapse
#print axioms weierstrass_chordRaw_of_X_ne
#print axioms weierstrass_chordRaw_of_X_eq
#print axioms weierstrass_chordRaw_ne_zero
#print axioms weierstrass_toAffine_chordRaw
#print axioms good_reduction_chord_origin_scalar
#print axioms good_reduction_shifted_relation
#print axioms origin_local_iff_fixed_transport
#print axioms collinear_triple_shifted_relation

end XedniChordBridge
