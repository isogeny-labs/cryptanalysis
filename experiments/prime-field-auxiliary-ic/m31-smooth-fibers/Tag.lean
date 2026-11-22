import Mathlib

namespace FiberTag

/-- Equality up to sign after multiplication detects kernel translates up to sign. -/
theorem tagEquiv {G : Type*} [AddCommGroup G] (m : ℕ) (a b : G) :
    (m • a = m • b ∨ m • a = -(m • b)) ↔
    (m • (a-b) = 0 ∨ m • (a+b) = 0) := by
  simp only [nsmul_sub, nsmul_add, sub_eq_zero, add_eq_zero_iff_eq_neg]
end FiberTag

/-- Given the census totals, the unmarked neighbors have lower lift frequency
than coordinates in entirely unmarked fibers. -/
theorem FiberTag.neighborComparison :
    (28155874-925398 : ℚ)/(32*1760190-1852867) <
    (268414441-28155874 : ℚ)/(32*(16777216-1760190)) := by norm_num
