module

public import Mathlib.Tactic.Abel

/-! A verified table hit after an additive offset gives a scalar for the original point. -/
namespace OffsetRecovery

public theorem from_shifted_table_hit {A : Type*} [AddCommGroup A]
    (G target : A) (knownScalar offset : ℤ)
    (hit : target + offset • G = knownScalar • G) :
    target = (knownScalar - offset) • G := by
  rw [sub_zsmul]
  calc
    target = (target + offset • G) - offset • G := by abel
    _ = knownScalar • G - offset • G := by rw [hit]
    _ = knownScalar • G + -(offset • G) := by simp [sub_eq_add_neg]

end OffsetRecovery

#print axioms OffsetRecovery.from_shifted_table_hit
