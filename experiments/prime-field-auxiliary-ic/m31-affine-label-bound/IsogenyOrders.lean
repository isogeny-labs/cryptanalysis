import Mathlib

namespace M31IsogenyOrders

/-- Equal squared extension traces force the positive Frobenius
discriminants A,B into the same rational square class: CrossCurve.discriminant
supplies the equality, with nonzero target multiplier x in positive degree. -/
theorem squareProduct {A B : ℕ} {x y : ℤ} (hx : x ≠ 0)
    (equal : (A : ℤ)*x^2 = (B : ℤ)*y^2) : IsSquare (A*B) := by
  apply Rat.isSquare_natCast_iff.mp
  have e : (A : ℚ)*(x : ℚ)^2 = (B : ℚ)*(y : ℚ)^2 := by exact_mod_cast equal
  have nz : (x : ℚ) ≠ 0 := by exact_mod_cast hx
  refine ⟨(B : ℚ)*y/x, ?_⟩
  push_cast
  field_simp
  linear_combination (B : ℚ)*e

abbrev fourP : ℕ := 4*2147483647
def disc (s : ℕ) := fourP-s^2

/-- Only absolute traces are needed. 92681 is floor(sqrt(4p)). -/
theorem hasseRange (s : ℕ) (h : s^2 ≤ fourP) : s < 92682 := by
  by_contra! big
  have lower := Nat.mul_self_le_mul_self big
  norm_num [fourP, pow_two] at h lower
  omega

private theorem firstScreen : ∀ s : Fin 92682,
    IsSquare (disc 21645 * disc s.val) → s.val = 21645 := by native_decide

private theorem secondScreen : ∀ s : Fin 92682,
    IsSquare (disc 22553 * disc s.val) → s.val = 22553 := by native_decide

theorem onlyTrace (t s : ℕ) (fixture : t = 21645 ∨ t = 22553) (hasse : s^2 ≤ fourP)
    {x y : ℤ} (ordinary : x ≠ 0)
    (matchDisc : (disc t : ℤ)*x^2 = (disc s : ℤ)*y^2) : s = t := by
  have square := squareProduct ordinary matchDisc
  rcases fixture with rfl | rfl
  · exact firstScreen ⟨s,hasseRange s hasse⟩ square
  · exact secondScreen ⟨s,hasseRange s hasse⟩ square

theorem oppositeOrders :
    2147483648-21645 = 53*40518151 ∧ Nat.Prime 40518151 ∧
    2147483648-22553 = 3*5*13*11012621 ∧ Nat.Prime 11012621 := by native_decide

end M31IsogenyOrders
