import Mathlib

/-!
Given a lift of one public preimage S of U under multiplication by b,
construct rational witnesses for any public aU+bV relation. The proof
preserves both point-matching conditions and the original coefficient vector.
-/

theorem one_point_curve_lift
    {K : Type*} [CommRing K] (x y A : K) :
    let B := y ^ 2 - x ^ 3 - A * x
    y ^ 2 = x ^ 3 + A * x + B := by
  dsimp
  ring

theorem one_point_coefficient_reduces
    {K : Type*} [CommRing K] (x y A B₀ : K)
    (hpoint : y ^ 2 = x ^ 3 + A * x + B₀) :
    y ^ 2 - x ^ 3 - A * x = B₀ := by
  linear_combination hpoint

theorem common_preimage_relation_lift
    {F R : Type*} [AddCommGroup F] [AddCommGroup R]
    (reduce : R →+ F) (a b : ℤ) (U V S : F) (T : R)
    (hU : b • S = U)
    (hT : reduce T = S)
    (hinj : Function.Injective (fun z : F => b • z))
    (hrel : a • U + b • V = 0) :
    ∃ P Q : R, reduce P = U ∧ reduce Q = V ∧ a • P + b • Q = 0 := by
  have hzero : a • S + V = 0 := by
    apply hinj
    calc
      b • (a • S + V) = a • (b • S) + b • V := by
        rw [smul_add, smul_smul, smul_smul, mul_comm b a]
      _ = 0 := by rw [hU]; exact hrel
      _ = b • (0 : F) := by simp
  have hV : (-a) • S = V := by
    rw [neg_smul]
    have hv : V = -(a • S) := add_left_cancel (calc
      a • S + V = 0 := hzero
      _ = a • S + -(a • S) := (add_neg_cancel _).symm)
    exact hv.symm
  refine ⟨b • T, (-a) • T, ?_, ?_, ?_⟩
  · simpa [map_zsmul, hT] using hU
  · simpa [map_zsmul, hT] using hV
  · calc
      a • (b • T) + b • ((-a) • T) = (a * b + b * (-a)) • T := by
        rw [smul_smul, smul_smul, add_smul]
      _ = (0 : ℤ) • T := by congr 1; ring
      _ = 0 := by simp

theorem public_relation_of_compatible_lift
    {F R : Type*} [AddCommGroup F] [AddCommGroup R]
    (reduce : R →+ F) (a b : ℤ) (U V : F) (P Q : R)
    (hP : reduce P = U) (hQ : reduce Q = V)
    (hrel : a • P + b • Q = 0) :
    a • U + b • V = 0 := by
  have h := congrArg reduce hrel
  simpa [map_add, map_zsmul, hP, hQ] using h

#print axioms common_preimage_relation_lift
#print axioms public_relation_of_compatible_lift
#print axioms one_point_curve_lift
#print axioms one_point_coefficient_reduces
