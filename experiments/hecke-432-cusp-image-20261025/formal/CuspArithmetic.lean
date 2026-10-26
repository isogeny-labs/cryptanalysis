import Mathlib.Data.Nat.Prime.Basic
import Mathlib.Tactic.Linarith

namespace CuspArithmetic

/-! The arithmetic obstruction used after good-reduction torsion injectivity.
    The elliptic-curve and modular-cusp bridges are recorded separately. -/
theorem no_torsion_prime_from_reduction_orders
    (l : Nat) (hl : Nat.Prime l)
    (atSeven : l ≠ 7 → l ∣ 7)
    (atThirteen : l ≠ 13 → l ∣ 9) : False := by
  by_cases h : l = 7
  · subst l
    have hdiv : 7 ∣ 9 := atThirteen (by decide)
    norm_num at hdiv
  · have hdiv : l ∣ 7 := atSeven h
    rcases (Nat.dvd_prime (by decide : Nat.Prime 7)).mp hdiv with hone | hseven
    · have htwo := hl.two_le
      omega
    · exact h hseven

theorem rational_cusps_count :
    1 + 1 + 2 + 2 + 1 + 2 + 1 + 2 + 2 + 1 + 2 + 1 + 2 + 2 + 1 + 1 = 24 := by
  norm_num

#print axioms no_torsion_prime_from_reduction_orders
#print axioms rational_cusps_count

end CuspArithmetic
