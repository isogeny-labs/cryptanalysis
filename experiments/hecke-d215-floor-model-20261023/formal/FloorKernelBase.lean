module

public import Mathlib.Tactic.Ring
public import Mathlib.Algebra.Ring.Rat

/-! Four disjoint signed floor certificates have unique coefficients.
The concrete 140-by-168 row matrix and its rank receipt are checked in Sage/Python;
they are not yet encoded as Lean definitions. -/

namespace FloorKernel

public theorem separating_coordinates {n : ℕ}
    (v0 v1 v2 v3 : Fin n → ℚ) (w0 w1 w2 w3 : Fin n)
    (h00 : v0 w0 ≠ 0) (h11 : v1 w1 ≠ 0)
    (h22 : v2 w2 ≠ 0) (h33 : v3 w3 ≠ 0)
    (h10 : v1 w0 = 0) (h20 : v2 w0 = 0) (h30 : v3 w0 = 0)
    (h01 : v0 w1 = 0) (h21 : v2 w1 = 0) (h31 : v3 w1 = 0)
    (h02 : v0 w2 = 0) (h12 : v1 w2 = 0) (h32 : v3 w2 = 0)
    (h03 : v0 w3 = 0) (h13 : v1 w3 = 0) (h23 : v2 w3 = 0)
    (a0 a1 a2 a3 : ℚ)
    (hcomb : ∀ x, a0 * v0 x + a1 * v1 x + a2 * v2 x + a3 * v3 x = 0) :
    a0 = 0 ∧ a1 = 0 ∧ a2 = 0 ∧ a3 = 0 := by
  have h0 := hcomb w0
  have h1 := hcomb w1
  have h2 := hcomb w2
  have h3 := hcomb w3
  simp [h10, h20, h30] at h0
  simp [h01, h21, h31] at h1
  simp [h02, h12, h32] at h2
  simp [h03, h13, h23] at h3
  exact ⟨h0.resolve_right h00,
         h1.resolve_right h11,
         h2.resolve_right h22,
         h3.resolve_right h33⟩

end FloorKernel

#print axioms FloorKernel.separating_coordinates
