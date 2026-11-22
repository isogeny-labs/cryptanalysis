import Std
import Init.Grind.Ring.Basic

namespace FreeCodeElimination
open Lean.Grind

def firstPairQuadratic {F : Type} [CommRing F] (C p H w : F) : F :=
  C*w*w + p*w + H

def eliminatedValue {F : Type} [CommRing F]
    (C p H r0 r1 : F) : F :=
  C*r0*r0 + p*r0*r1 + H*r1*r1

/-- The norm of a linear remainder modulo a split quadratic. The source
pair coefficient identities are explicit hypotheses. -/
theorem split_quadratic_norm {F : Type} [CommRing F]
    (C p H r0 r1 w0 w1 : F)
    (hsum : C*(w0+w1)=p) (hprod : C*w0*w1=H) :
    C*(r0+r1*w0)*(r0+r1*w1) = eliminatedValue C p H r0 r1 := by
  dsimp [eliminatedValue]
  grind +ring

/-- If the quadratic splits at its two listed field roots and the quartic
has a linear remainder there, the eliminated value vanishes exactly when
the two polynomials have a common field root. -/
theorem eliminated_zero_iff_shared_root {F : Type} [Field F]
    (C p H r0 r1 w0 w1 : F) (q s : F → F)
    (hC : C ≠ 0)
    (hsum : C*(w0+w1)=p) (hprod : C*w0*w1=H)
    (hfactor : ∀ w, firstPairQuadratic C p H w = C*(w-w0)*(w-w1))
    (hrem : ∀ w, q w = firstPairQuadratic C p H w * s w + r0+r1*w) :
    eliminatedValue C p H r0 r1 = 0 ↔
      ∃ w, firstPairQuadratic C p H w = 0 ∧ q w = 0 := by
  have hnorm := split_quadratic_norm C p H r0 r1 w0 w1 hsum hprod
  constructor
  · intro h
    have hmul : C*(r0+r1*w0)*(r0+r1*w1)=0 := by rw [hnorm]; exact h
    rcases Field.of_mul_eq_zero hmul with hleft | hright
    · rcases Field.of_mul_eq_zero hleft with hc | h0
      · exact False.elim (hC hc)
      · refine ⟨w0, ?_, ?_⟩
        · rw [hfactor]; grind +ring
        · rw [hrem]; rw [hfactor]; grind +ring
    · refine ⟨w1, ?_, ?_⟩
      · rw [hfactor]; grind +ring
      · rw [hrem]; rw [hfactor]; grind +ring
  · rintro ⟨w, hw, hq⟩
    rw [hfactor w] at hw
    rcases Field.of_mul_eq_zero hw with hleft | hright
    · rcases Field.of_mul_eq_zero hleft with hc | h0
      · exact False.elim (hC hc)
      · have heq : w = w0 := by grind +ring
        subst w
        have hr : r0+r1*w0=0 := by
          rw [hrem] at hq
          grind +ring
        rw [← hnorm]
        grind +ring
    · have heq : w = w1 := by grind +ring
      subst w
      have hr : r0+r1*w1=0 := by
        rw [hrem] at hq
        grind +ring
      rw [← hnorm]
      grind +ring

#print axioms split_quadratic_norm
#print axioms eliminated_zero_iff_shared_root

end FreeCodeElimination
