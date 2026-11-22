import Mathlib

/-!
Given a rational lift of one public point and *known* coefficients a,b,
the multiples bT and -aT realize the same public two-point relation exactly.
The elliptic-curve construction of T and its good reduction are separate
arithmetic obligations, recorded alongside the experiment.
-/

namespace XedniKnownRelationLifts

theorem common_point_of_known_relation
    {C : Type*} [AddCommGroup C]
    (U V : C) (q a b c d : ℤ)
    (hqU : q • U = 0) (hqV : q • V = 0)
    (hrelation : a • U + b • V = 0)
    (hbezout : b * c + q * d = 1) :
    b • (c • U) = U ∧ (-a) • (c • U) = V := by
  have hbU : b • (c • U) = U := by
    have h := congrArg (fun n : ℤ => n • U) hbezout
    have hqd : (q * d) • U = 0 := by
      rw [mul_comm q d, ← smul_smul, hqU, smul_zero]
    simpa only [add_smul, one_smul, hqd, add_zero, smul_smul] using h
  have hqR : q • (c • U) = 0 := by
    rw [smul_smul, mul_comm q c, ← smul_smul, hqU, smul_zero]
  let X : C := V + a • (c • U)
  have hqX : q • X = 0 := by
    simp only [X, smul_add, hqV, zero_add]
    rw [smul_comm q a (c • U), hqR, smul_zero]
  have hab : b • (a • (c • U)) = a • U := by
    rw [smul_comm b a (c • U), hbU]
  have hbX : b • X = 0 := by
    calc
      b • X = b • V + b • (a • (c • U)) := by
        change b • (V + a • (c • U)) = _
        rw [smul_add]
      _ = b • V + a • U := by rw [hab]
      _ = 0 := by rw [add_comm]; exact hrelation
  have hzero : X = 0 := by
    have h := congrArg (fun n : ℤ => n • X) hbezout
    have hbc : (b * c) • X = 0 := by
      rw [mul_comm b c, ← smul_smul, hbX, smul_zero]
    have hqd : (q * d) • X = 0 := by
      rw [mul_comm q d, ← smul_smul, hqX, smul_zero]
    have hh : (b * c) • X + (q * d) • X = X := by
      simpa only [add_smul, one_smul] using h
    rw [hbc, hqd, add_zero] at hh
    exact hh.symm
  constructor
  · exact hbU
  · calc
      (-a) • (c • U) = -(a • (c • U)) := by rw [neg_smul]
      _ = V := by simp only [X] at hzero; exact (eq_neg_of_add_eq_zero_left hzero).symm

theorem exact_relation_from_common_lift
    {C H : Type*} [AddCommGroup C] [AddCommGroup H]
    (reduce : H →+ C) (T : H) (U V : C) (a b : ℤ)
    (hU : b • reduce T = U) (hV : (-a) • reduce T = V) :
    ∃ P Q : H, reduce P = U ∧ reduce Q = V ∧ a • P + b • Q = 0 := by
  refine ⟨b • T, (-a) • T, ?_, ?_, ?_⟩
  · simpa only [map_zsmul] using hU
  · simpa only [map_zsmul] using hV
  · rw [smul_smul, smul_smul]
    have hm : b * -a = -(a * b) := by ring
    rw [hm, neg_smul]
    exact add_neg_cancel _

theorem interpolated_coefficient_congruence
    (p : ℤ) (A B₀ x y : ℤ)
    (hpoint : p ∣ y ^ 2 - (x ^ 3 + A * x + B₀)) :
    p ∣ (y ^ 2 - x ^ 3 - A * x) - B₀ := by
  convert hpoint using 1
  ring

#print axioms common_point_of_known_relation
#print axioms exact_relation_from_common_lift
#print axioms interpolated_coefficient_congruence

end XedniKnownRelationLifts
