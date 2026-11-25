import Mathlib.Algebra.Polynomial.FieldDivision

namespace RootIntersection
open Polynomial

theorem gcd_root {K : Type*} [Field K] [GCDMonoid K[X]] (b q : K[X]) (x : K) :
    IsRoot (GCDMonoid.gcd b q) x ↔ IsRoot b x ∧ IsRoot q x := by
  simp only [← dvd_iff_isRoot, dvd_gcd_iff]

theorem evaluate_on_basis {K : Type*} [Field K] [GCDMonoid K[X]]
    (b q : K[X]) (x : K) (h : IsRoot b x) :
    IsRoot (GCDMonoid.gcd b q) x ↔ q.eval x = 0 := by
  rw [gcd_root, and_iff_right h]
  rfl

end RootIntersection
