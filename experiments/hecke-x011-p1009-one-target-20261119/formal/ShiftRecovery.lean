import Mathlib

namespace X011Target

/-- A prepared point log and a verified additive shift determine the public log. -/
theorem shift_recovery {A : Type*} [AddCommGroup A] (Q G P : A) (k l : ℤ)
    (prepared : P = l • G) (hit : Q + k • G = P) : Q = (l - k) • G := by
  rw [prepared] at hit
  rw [sub_zsmul]
  simpa only [sub_eq_add_neg] using (eq_sub_of_add_eq hit)

#print axioms shift_recovery

end X011Target
