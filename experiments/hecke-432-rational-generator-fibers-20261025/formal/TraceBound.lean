import Mathlib.Tactic.Linarith

/-! Numeric Hasse-window consequence of a scalar Frobenius action at level 432. -/

namespace TraceBound

theorem rational_generator_trace (t : ℤ)
    (hlo : -59 ≤ t) (hhi : t ≤ 59)
    (hcharpoly : 432 ∣ 884 - t) : t = 20 := by
  rcases hcharpoly with ⟨k, hk⟩
  omega

theorem negative_generator_trace (t : ℤ)
    (hlo : -59 ≤ t) (hhi : t ≤ 59)
    (hcharpoly : 432 ∣ 884 + t) : t = -20 := by
  rcases hcharpoly with ⟨k, hk⟩
  omega

#print axioms rational_generator_trace
#print axioms negative_generator_trace

end TraceBound
