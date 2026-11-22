import Std
import Init.Grind.Ring.Basic

namespace DirectRoot
open Lean.Grind

def poly4 {R : Type} [CommRing R] (c0 c1 c2 c3 c4 w : R) : R :=
  c0 + c1*w + c2*w*w + c3*w*w*w + c4*w*w*w*w

def horner4 {R : Type} [CommRing R] (c0 c1 c2 c3 c4 w : R) : R :=
  (((c4*w+c3)*w+c2)*w+c1)*w+c0

/-- The circuit's four multiply-add steps evaluate the source quartic. -/
theorem horner4_eq_poly4 {R : Type} [CommRing R]
    (c0 c1 c2 c3 c4 w : R) :
    horner4 c0 c1 c2 c3 c4 w = poly4 c0 c1 c2 c3 c4 w := by
  unfold horner4 poly4
  grind +ring

/-- Two direct Horner zero tests have exactly the common-root witnesses. -/
theorem two_horner_zeros_iff_common_root {R : Type} [CommRing R]
    (f0 f1 f2 f3 f4 g0 g1 g2 g3 g4 : R) :
    (∃ w : R, horner4 f0 f1 f2 f3 f4 w=0 ∧
              horner4 g0 g1 g2 g3 g4 w=0) ↔
    (∃ w : R, poly4 f0 f1 f2 f3 f4 w=0 ∧
              poly4 g0 g1 g2 g3 g4 w=0) := by
  constructor
  · rintro ⟨w,hf,hg⟩
    exact ⟨w, (horner4_eq_poly4 f0 f1 f2 f3 f4 w).symm ▸ hf,
              (horner4_eq_poly4 g0 g1 g2 g3 g4 w).symm ▸ hg⟩
  · rintro ⟨w,hf,hg⟩
    exact ⟨w, (horner4_eq_poly4 f0 f1 f2 f3 f4 w) ▸ hf,
              (horner4_eq_poly4 g0 g1 g2 g3 g4 w) ▸ hg⟩

#print axioms DirectRoot.horner4_eq_poly4
#print axioms DirectRoot.two_horner_zeros_iff_common_root

end DirectRoot
