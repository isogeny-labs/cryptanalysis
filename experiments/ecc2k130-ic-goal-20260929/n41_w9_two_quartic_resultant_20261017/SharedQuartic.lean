import Std
import Init.Grind.Ring.Basic

namespace SharedQuartic
open Lean.Grind

/-- The target-conditioned gate after eliminating a shared coordinate from
two quartics when the second quartic splits into four known field roots. -/
def gate {F : Type} [Mul F] (R3 : F → F → F) (z r0 r1 r2 r3 : F) : F :=
  R3 z r0 * R3 z r1 * R3 z r2 * R3 z r3

/-- The leading-coefficient expression is one field square in
characteristic two. This is the tested zero criterion in the census. -/
theorem quartic_lead_square {F : Type} [CommRing F]
    (charTwo : ∀ x : F, x+x=0) (w p h c : F) :
    w*w*p*p + (h*w*w+c)*(h*w*w+c) =
      (w*p+h*w*w+c)*(w*p+h*w*w+c) := by
  have hz := charTwo ((w*p)*(h*w*w+c))
  grind +ring

/-- A split quartic has exactly its four listed roots. Repetitions are allowed. -/
theorem split_quartic_roots {F : Type} [Field F]
    (R4 : F → F) (c r0 r1 r2 r3 : F) (hc : c ≠ 0)
    (hfactor : ∀ w, R4 w = c * (w-r0) * (w-r1) * (w-r2) * (w-r3))
    (w : F) :
    R4 w = 0 ↔ w = r0 ∨ w = r1 ∨ w = r2 ∨ w = r3 := by
  rw [hfactor w]
  constructor
  · intro h
    rcases Field.of_mul_eq_zero h with h | h3
    · rcases Field.of_mul_eq_zero h with h | h2
      · rcases Field.of_mul_eq_zero h with h | h1
        · rcases Field.of_mul_eq_zero h with h | h0
          · exact False.elim (hc h)
          · left; grind +ring
        · exact Or.inr (Or.inl (by grind +ring))
      · exact Or.inr (Or.inr (Or.inl (by grind +ring)))
    · exact Or.inr (Or.inr (Or.inr (by grind +ring)))
  · intro h
    rcases h with h | h | h | h <;> subst w <;> grind +ring

/-- Exact shared-root criterion for the finite-root quartic gate. The
factorization hypothesis is what connects the gate to the actual quartic. -/
theorem gate_zero_iff_common_root {F : Type} [Field F]
    (R3 : F → F → F) (R4 : F → F)
    (c r0 r1 r2 r3 z : F) (hc : c ≠ 0)
    (hfactor : ∀ w, R4 w = c * (w-r0) * (w-r1) * (w-r2) * (w-r3)) :
    gate R3 z r0 r1 r2 r3 = 0 ↔
      ∃ w, R3 z w = 0 ∧ R4 w = 0 := by
  have hr := split_quartic_roots R4 c r0 r1 r2 r3 hc hfactor
  constructor
  · intro h
    dsimp [gate] at h
    rcases Field.of_mul_eq_zero h with h | h3
    · rcases Field.of_mul_eq_zero h with h | h2
      · rcases Field.of_mul_eq_zero h with h0 | h1
        · exact ⟨r0, h0, (hr r0).2 (Or.inl rfl)⟩
        · exact ⟨r1, h1, (hr r1).2 (Or.inr (Or.inl rfl))⟩
      · exact ⟨r2, h2, (hr r2).2 (Or.inr (Or.inr (Or.inl rfl)))⟩
    · exact ⟨r3, h3, (hr r3).2 (Or.inr (Or.inr (Or.inr rfl)))⟩
  · rintro ⟨w, hw, hroot⟩
    rcases (hr w).1 hroot with h0 | h1 | h2 | h3
    · subst w; simp [gate, hw]; grind +ring
    · subst w; simp [gate, hw]; grind +ring
    · subst w; simp [gate, hw]; grind +ring
    · subst w; simp [gate, hw]; grind +ring

#print axioms SharedQuartic.split_quartic_roots
#print axioms SharedQuartic.gate_zero_iff_common_root
#print axioms SharedQuartic.quartic_lead_square

end SharedQuartic
