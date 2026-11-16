import AdaptiveInverseLift
import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace XedniVectorDependentRankOneLift

/-- A detected public relation supplies a common cyclic preimage. -/
theorem public_factorization {K : Type*} [Field K]
    (a b U V : K) (hb : b ≠ 0) (hrel : a * U + b * V = 0) :
    b * (U / b) = U ∧ (-a) * (U / b) = V := by
  constructor
  · field_simp [hb]
  · have hv : -a * U = b * V := by linear_combination -hrel
    calc
      (-a) * (U / b) = ((-a) * U) / b := by ring
      _ = (b * V) / b := by rw [hv]
      _ = V := by field_simp [hb]

/-- Any common rational generator yields the requested coefficient relation. -/
theorem rank_one_relation {A : Type*} [AddCommGroup A]
    (P : A) (a b : ℤ) :
    a • (b • P) + b • ((-a) • P) = 0 := by
  calc
    a • (b • P) + b • ((-a) • P) = (a * b + b * (-a)) • P := by
      rw [add_smul, smul_smul, smul_smul]
    _ = 0 := by rw [show a * b + b * (-a) = 0 by ring, zero_smul]

/-- In a public group where multiplication by `b` is bijective, the public
relation is exactly the condition for a common rank-one preimage. -/
theorem public_relation_iff_rank_one {A : Type*} [AddCommGroup A]
    (a b : ℤ) (U V : A)
    (hb : Function.Bijective (fun T : A => b • T)) :
    a • U + b • V = 0 ↔
      ∃ T : A, b • T = U ∧ (-a) • T = V := by
  constructor
  · intro hrel
    obtain ⟨T, hT⟩ := hb.2 U
    refine ⟨T, hT, ?_⟩
    have hrel' : b • (a • T + V) = 0 := by
      calc
        b • (a • T + V) = a • U + b • V := by
          rw [smul_add, ← hT, smul_smul, smul_smul, mul_comm]
        _ = 0 := hrel
    have hzero : a • T + V = 0 := hb.1 (by simpa using hrel')
    simpa only [neg_smul] using neg_eq_of_add_eq_zero_right hzero
  · rintro ⟨T, hU, hV⟩
    rw [← hU, ← hV]
    exact rank_one_relation T a b

/-- A Bézout certificate gives an explicit inverse to multiplication by `b`
on a group killed by `q`. -/
theorem coefficient_bijective_of_torsion {A : Type*} [AddCommGroup A]
    (q : ℕ) (b c d : ℤ)
    (hbez : b * c + (q : ℤ) * d = 1)
    (htors : ∀ X : A, (q : ℤ) • X = 0) :
    Function.Bijective (fun X : A => b • X) := by
  have hbc (X : A) : b • (c • X) = X := by
    have h : (b * c + (q : ℤ) * d) • X = X := by rw [hbez, one_smul]
    rw [add_smul, mul_smul, mul_smul, htors, add_zero] at h
    exact h
  have hcb (X : A) : c • (b • X) = X := by
    simpa only [smul_smul, mul_comm] using hbc X
  constructor
  · intro X Y hXY
    change b • X = b • Y at hXY
    calc
      X = c • (b • X) := (hcb X).symm
      _ = c • (b • Y) := by rw [hXY]
      _ = Y := hcb Y
  · intro Y
    exact ⟨c • Y, hbc Y⟩

/-- In a `q`-torsion public group, a Bézout-invertible coefficient makes the
public relation equivalent to the common rank-one preimage construction. -/
theorem torsion_public_relation_iff_rank_one {A : Type*} [AddCommGroup A]
    (q : ℕ) (a b c d : ℤ) (U V : A)
    (hbez : b * c + (q : ℤ) * d = 1)
    (htors : ∀ X : A, (q : ℤ) • X = 0) :
    a • U + b • V = 0 ↔
      ∃ T : A, b • T = U ∧ (-a) • T = V := by
  exact public_relation_iff_rank_one a b U V
    (coefficient_bijective_of_torsion q b c d hbez htors)

/-- Apply the group identity to the explicitly constructed rational point. -/
theorem rational_rank_one_relation (x y a b : ℤ) :
    a • (b • XedniAdaptiveInverseLift.liftPos x y) +
    b • ((-a) • XedniAdaptiveInverseLift.liftPos x y) = 0 := by
  exact rank_one_relation (XedniAdaptiveInverseLift.liftPos x y) a b

/-- Every additive reduction map commutes with both constructed multiples. -/
theorem rank_one_reduction_commutes {H A : Type*}
    [AddCommGroup H] [AddCommGroup A]
    (ρ : H →+ A) (P : H) (a b : ℤ) :
    ρ (b • P) = b • ρ P ∧ ρ ((-a) • P) = (-a) • ρ P := by
  constructor <;> simp

/-- The reduced constructed pair retains the coefficient relation. -/
theorem rank_one_reduced_relation {H A : Type*}
    [AddCommGroup H] [AddCommGroup A]
    (ρ : H →+ A) (P : H) (a b : ℤ) :
    a • ρ (b • P) + b • ρ ((-a) • P) = 0 := by
  simpa only [map_zsmul] using rank_one_relation (ρ P) a b

/-- The fixed reduced Weierstrass model has integral discriminant `-1664`. -/
theorem baseModel_discriminant (p : ℕ) :
    (XedniAdaptiveInverseLift.baseModel p).Δ = (-1664 : ZMod p) := by
  norm_num [XedniAdaptiveInverseLift.baseModel,
    WeierstrassCurve.Δ, WeierstrassCurve.b₂,
    WeierstrassCurve.b₄, WeierstrassCurve.b₆,
    WeierstrassCurve.b₈]

/-- The fixed reduced model is elliptic at every prime not dividing `1664`. -/
theorem baseModel_isElliptic (p : ℕ) [Fact p.Prime]
    (hp : ¬ p ∣ 1664) :
    (XedniAdaptiveInverseLift.baseModel p).IsElliptic := by
  have hne : (1664 : ZMod p) ≠ 0 := by
    intro h
    exact hp ((ZMod.natCast_eq_zero_iff 1664 p).mp h)
  refine ⟨isUnit_iff_ne_zero.mpr ?_⟩
  rw [baseModel_discriminant]
  exact neg_ne_zero.mpr hne

/-- All eight frozen field primes give an elliptic reduced model. -/
theorem panel_baseModel_isElliptic (p : ℕ)
    (hpanel : p = 47 ∨ p = 101 ∨ p = 191 ∨ p = 211 ∨
      p = 251 ∨ p = 281 ∨ p = 347 ∨ p = 349) :
    (XedniAdaptiveInverseLift.baseModel p).IsElliptic := by
  have hprime : p.Prime := by
    rcases hpanel with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl <;> norm_num
  letI : Fact p.Prime := ⟨hprime⟩
  apply baseModel_isElliptic p
  rcases hpanel with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl <;> norm_num

/-- The centered integer coordinates satisfy the exact finite curve equation. -/
theorem reduced_generator_equation {p : ℕ} (x y : ℤ)
    (hpoint : (y : ZMod p) ^ 2 =
      (x : ZMod p) ^ 3 - (x : ZMod p) - 2) :
    (XedniAdaptiveInverseLift.baseModel p).Equation
      (x : ZMod p) (y : ZMod p) := by
  simp only [XedniAdaptiveInverseLift.baseModel,
    WeierstrassCurve.Affine.equation_iff]
  linear_combination hpoint

/-- The public finite point named by the centered coordinates. -/
def reducedGenerator (p : ℕ) [Nontrivial (ZMod p)]
    [(XedniAdaptiveInverseLift.baseModel p).IsElliptic]
    (x y : ℤ)
    (hpoint : (y : ZMod p) ^ 2 =
      (x : ZMod p) ^ 3 - (x : ZMod p) - 2) :
    (XedniAdaptiveInverseLift.baseModel p).Point :=
  WeierstrassCurve.Affine.Point.mk (reduced_generator_equation x y hpoint)

/-- The named finite point has precisely the selected affine coordinates. -/
theorem reducedGenerator_coordinates (p : ℕ) [Nontrivial (ZMod p)]
    [(XedniAdaptiveInverseLift.baseModel p).IsElliptic]
    (x y : ℤ)
    (hpoint : (y : ZMod p) ^ 2 =
      (x : ZMod p) ^ 3 - (x : ZMod p) - 2) :
    WeierstrassCurve.Affine.pointEquiv
      (XedniAdaptiveInverseLift.baseModel p)
      (reducedGenerator p x y hpoint) =
      .some ⟨((x : ZMod p), (y : ZMod p)),
        reduced_generator_equation x y hpoint⟩ := by
  rfl

#print axioms public_factorization
#print axioms public_relation_iff_rank_one
#print axioms coefficient_bijective_of_torsion
#print axioms torsion_public_relation_iff_rank_one
#print axioms rank_one_relation
#print axioms rational_rank_one_relation
#print axioms rank_one_reduction_commutes
#print axioms rank_one_reduced_relation
#print axioms baseModel_discriminant
#print axioms baseModel_isElliptic
#print axioms panel_baseModel_isElliptic
#print axioms reduced_generator_equation
#print axioms reducedGenerator_coordinates
#print axioms XedniAdaptiveInverseLift.rational_model
#print axioms XedniAdaptiveInverseLift.reduction_model

end XedniVectorDependentRankOneLift
