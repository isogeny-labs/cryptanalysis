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

/-- Apply the group identity to the explicitly constructed rational point. -/
theorem rational_rank_one_relation (x y a b : ℤ) :
    a • (b • XedniAdaptiveInverseLift.liftPos x y) +
    b • ((-a) • XedniAdaptiveInverseLift.liftPos x y) = 0 := by
  exact rank_one_relation (XedniAdaptiveInverseLift.liftPos x y) a b

#print axioms public_factorization
#print axioms rank_one_relation
#print axioms rational_rank_one_relation
#print axioms XedniAdaptiveInverseLift.rational_model
#print axioms XedniAdaptiveInverseLift.reduction_model

end XedniVectorDependentRankOneLift
