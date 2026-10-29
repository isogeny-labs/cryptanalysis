import Mathlib.Algebra.Field.ZMod
import Mathlib.Algebra.Module.LinearMap.Basic

namespace J1728Frobenius

private theorem no_square_neg_one : ∀ a : ZMod 3, a * a ≠ -1 := by
  decide

/-- A linear operator whose square is negative identity has no nonzero
    eigenvector over `F₃`. This is the finite-dimensional algebraic gate for
    Frobenius acting on a rational cyclic 3-kernel when `p ≡ 1 (mod 3)` and
    the elliptic-curve trace is zero. -/
theorem no_rational_eigenline
    {V : Type*} [AddCommGroup V] [Module (ZMod 3) V]
    (frobenius : V →ₗ[ZMod 3] V)
    (square_eq_neg : ∀ v : V, frobenius (frobenius v) = -v)
    (v : V) (v_ne_zero : v ≠ 0) (eigenvalue : ZMod 3) :
    frobenius v ≠ eigenvalue • v := by
  intro eigen
  have composed : frobenius (frobenius v) = (eigenvalue * eigenvalue) • v := by
    calc
      frobenius (frobenius v) = frobenius (eigenvalue • v) := congrArg frobenius eigen
      _ = eigenvalue • frobenius v := map_smul frobenius eigenvalue v
      _ = eigenvalue • (eigenvalue • v) := by rw [eigen]
      _ = (eigenvalue * eigenvalue) • v := by rw [mul_smul]
  have scalar_eq : (eigenvalue * eigenvalue + 1) • v = 0 := by
    calc
      (eigenvalue * eigenvalue + 1) • v = (eigenvalue * eigenvalue) • v + (1 : ZMod 3) • v := by rw [add_smul]
      _ = -v + v := by rw [← composed, square_eq_neg, one_smul]
      _ = 0 := neg_add_cancel v
  have scalar_ne_zero : eigenvalue * eigenvalue + 1 ≠ 0 := by
    intro scalar_zero
    apply no_square_neg_one eigenvalue
    exact (add_eq_zero_iff_eq_neg.mp scalar_zero)
  have v_eq_zero : v = 0 := by
    have scaled := congrArg (fun w : V => (eigenvalue * eigenvalue + 1)⁻¹ • w) scalar_eq
    simpa [← mul_smul, inv_mul_cancel₀ scalar_ne_zero] using scaled
  exact v_ne_zero v_eq_zero

theorem no_stable_cyclic_three_line
    {V : Type*} [AddCommGroup V] [Module (ZMod 3) V]
    (frobenius : V →ₗ[ZMod 3] V)
    (square_eq_neg : ∀ v : V, frobenius (frobenius v) = -v)
    (v : V) (v_ne_zero : v ≠ 0)
    (stable : ∃ eigenvalue : ZMod 3, frobenius v = eigenvalue • v) : False := by
  obtain ⟨eigenvalue, eigen⟩ := stable
  exact no_rational_eigenline frobenius square_eq_neg v v_ne_zero eigenvalue eigen

#print axioms no_rational_eigenline
#print axioms no_stable_cyclic_three_line

end J1728Frobenius
