import Mathlib.Tactic

namespace PublicCoset
variable {G : Type*} [AddCommGroup G]

/-- Extend an indexed prefix by appending its translate. -/
def expand (t g : G) : Nat → Nat → G
  | 0, _ => t
  | k+1, i =>
      if i < 2^k then expand t g k i
      else expand t g k (i-2^k) + (2^k : Nat) • g

theorem ordered (t g : G) (k i : Nat) (hi : i < 2^k) :
    expand t g k i = t + i • g := by
  induction k generalizing i with
  | zero =>
    have hz : i = 0 := by simpa using hi
    simp [hz, expand]
  | succ k ih =>
    by_cases h : i < 2^k
    · simpa [expand, h] using ih i h
    · have rem : i - 2^k < 2^k := by rw [pow_succ] at hi; omega
      simp only [expand, if_neg h, ih _ rem, add_assoc, ← add_nsmul]
      rw [Nat.sub_add_cancel (by omega)]

#print axioms ordered
end PublicCoset
