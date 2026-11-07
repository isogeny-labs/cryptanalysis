module

public import Mathlib.Tactic.Abel

/-! The algebraic uniqueness step for the Fricke action on X₀(11).
The identification of the modular curve and its automorphism group is a
separate mathematical input, described in RESULT.md. -/
namespace FrickeAffine

variable {A : Type*} [AddCommGroup A]

/-- An affine map with linear part `±1` which exchanges the origin and a
point of order greater than two must have linear part `-1`. -/
theorem from_cusp_exchange (T : A) (u : A →+ A)
    (hlinear : (∀ P, u P = P) ∨ (∀ P, u P = -P))
    (hswap : T + u T = 0) (hnot_two : T + T ≠ 0) :
    ∀ P, T + u P = T - P := by
  rcases hlinear with hplus | hminus
  · have htwo : T + T = 0 := by simpa [hplus T] using hswap
    exact False.elim (hnot_two htwo)
  · intro P
    rw [hminus P]
    abel

/-- The resulting affine map is an involution and exchanges the two cusps. -/
theorem affine_involution (T P : A) : T - (T - P) = P := by
  abel

theorem cusp_infinity_image (T : A) : T - (0 : A) = T := by
  abel

theorem cusp_zero_image (T : A) : T - T = 0 := by
  abel

#print axioms from_cusp_exchange
#print axioms affine_involution
#print axioms cusp_infinity_image
#print axioms cusp_zero_image

end FrickeAffine
