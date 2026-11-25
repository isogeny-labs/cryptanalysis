import Mathlib.Tactic

namespace OrbitLanes
abbrev p := 2147483647

/-- Logical rotation expressed by separating the two nonoverlapping
bit fields. The six shift widths are those used by the native traversal. -/
theorem rotate_eq (x k : ℕ) (hx : x < p)
    (hk : k = 1 ∨ k = 2 ∨ k = 3 ∨ k = 4 ∨ k = 8 ∨ k = 12) :
    2^k * (x % 2^(31-k)) + x / 2^(31-k) = (2^k*x) % p := by
  rcases hk with h|h|h|h|h|h <;> subst k <;> norm_num [p] at * <;> omega

/-- Advancing four coordinates advances their squares and cubes by
eight and twelve binary places respectively, including wraparound. -/
theorem advance (x : ZMod p) :
    ((2^4*x)^2, (2^4*x)^3) = (2^8*x^2, 2^12*x^3) := by
  apply Prod.ext <;> dsimp <;> ring

#print axioms rotate_eq
#print axioms advance
end OrbitLanes
