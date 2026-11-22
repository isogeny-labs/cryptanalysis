import Mathlib

namespace X011NoncyclicTarget

/-- A verified shift transports both coordinates in an additive group. -/
theorem pair_shift_recovery {A : Type*} [AddCommGroup A] (Q P G H : A) (k a b : ℤ)
    (prepared : P = a • G + b • H) (hit : Q + k • G = P) :
    Q = (a - k) • G + b • H := by
  rw [prepared] at hit
  calc
    Q = (a • G + b • H) - k • G := eq_sub_of_add_eq hit
    _ = (a • G - k • G) + b • H := by abel
    _ = (a - k) • G + b • H := by
      rw [sub_zsmul]
      simp only [sub_eq_add_neg]

#print axioms pair_shift_recovery

end X011NoncyclicTarget
