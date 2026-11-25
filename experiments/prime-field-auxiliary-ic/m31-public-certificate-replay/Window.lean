import Mathlib

namespace PublicReplay

/-- A lookup at the low five bits and a recursive lookup at the next position
reconstruct the same scalar multiple in any additive commutative monoid. -/
theorem windowStep {G : Type*} [AddCommMonoid G] (k : ℕ) (P : G) :
    (k % 32) • P + (k / 32) • (32 • P) = k • P := by
  rw [← mul_smul, ← add_smul]
  congr 1
  omega

end PublicReplay
