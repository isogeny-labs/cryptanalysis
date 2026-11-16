import Mathlib

/-!
An abstract statement of the precommitted rank-one lift's information order.
The candidate rational relation is automatic. Once the first reduction is
fixed, matching the second public point is equivalent to the public relation
provided multiplication by b is injective in the finite target group.
-/

theorem precommitted_rank_one_relation
    {R : Type*} [AddCommGroup R] (P : R) (a b : ℤ) :
    a • (b • P) + b • ((-a) • P) = 0 := by
  rw [← mul_zsmul, ← mul_zsmul, ← add_zsmul]
  have h : a * b + -(b * a) = 0 := by ring
  simp [h]

theorem precommitted_second_reduction_iff_public
    {R F : Type*} [AddCommGroup R] [AddCommGroup F]
    (reduce : R →+ F) (P : R) (U V : F) (a b : ℤ)
    (hU : b • reduce P = U)
    (hinj : ∀ x : F, b • x = 0 → x = 0) :
    reduce ((-a) • P) = V ↔ a • U + b • V = 0 := by
  constructor
  · intro hV
    calc
      a • U + b • V = a • (b • reduce P) + b • ((-a) • reduce P) := by
        rw [hU, ← map_zsmul, hV]
      _ = 0 := precommitted_rank_one_relation (reduce P) a b
  · intro hrel
    have hzero : b • (V - reduce ((-a) • P)) = 0 := by
      rw [map_zsmul, smul_sub, ← mul_zsmul]
      have hcomm : b * -a = -(a * b) := by ring
      rw [hcomm, neg_zsmul, sub_neg_eq_add]
      rw [mul_zsmul, hU]
      simpa [add_comm] using hrel
    exact (sub_eq_zero.mp (hinj _ hzero)).symm

theorem precommitted_acceptance_iff_public
    {R F : Type*} [AddCommGroup R] [AddCommGroup F]
    (reduce : R →+ F) (P : R) (U V : F) (a b : ℤ)
    (hU : b • reduce P = U)
    (hinj : ∀ x : F, b • x = 0 → x = 0) :
    (reduce (b • P) = U ∧ reduce ((-a) • P) = V) ↔
      a • U + b • V = 0 := by
  have hfirst : reduce (b • P) = U := by simpa using hU
  simpa [hfirst] using precommitted_second_reduction_iff_public reduce P U V a b hU hinj

#print axioms precommitted_rank_one_relation
#print axioms precommitted_second_reduction_iff_public
#print axioms precommitted_acceptance_iff_public
