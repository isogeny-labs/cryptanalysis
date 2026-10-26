import Mathlib.Data.Fintype.Card
import Mathlib.Data.Finset.Card
import Mathlib.Data.Finset.Image
import Mathlib.Tactic.Linarith

namespace Prime997FiberSaturation

/- If one E fiber contains 72 rational sources and lies over three rational
   B points, each B fiber saturates the geometric degree bound 24. -/
theorem three_lifts_saturate
    (a b c : ℕ) (ha : a ≤ 24) (hb : b ≤ 24) (hc : c ≤ 24)
    (hprojected : a + b + c = 72) :
    a = 24 ∧ b = 24 ∧ c = 24 := by
  omega

/- A 12-point projected fiber cannot consist solely of complete
   24-point B fibers, regardless of how its sources split across lifts. -/
theorem twelve_forces_partial_lift
    (a b c : ℕ) (hprojected : a + b + c = 12) :
    (0 < a ∧ a < 24) ∨ (0 < b ∧ b < 24) ∨ (0 < c ∧ c < 24) := by
  omega

theorem forty_eight_needs_two_lifts
    (a b c : ℕ) (ha : a ≤ 24) (hb : b ≤ 24) (hc : c ≤ 24)
    (hprojected : a + b + c = 48) :
    (0 < a ∧ 0 < b) ∨ (0 < a ∧ 0 < c) ∨ (0 < b ∧ 0 < c) := by
  omega

theorem projected_histogram_lower_bound : 6 * 1 + 60 * 1 + 6 * 2 = 78 := by
  omega

theorem complement_bounds (fullImage : ℕ)
    (hlo : 79 ≤ fullImage) (hhi : fullImage ≤ 217) :
    791 ≤ 1008 - fullImage ∧ 1008 - fullImage ≤ 929 := by
  omega

#print axioms three_lifts_saturate
#print axioms twelve_forces_partial_lift
#print axioms forty_eight_needs_two_lifts
#print axioms projected_histogram_lower_bound
#print axioms complement_bounds

end Prime997FiberSaturation
