import Std
import Init.Grind.Ring.Basic

namespace OrderSymmetry
open Lean.Grind

/-- The exact polynomial shape used for the first-three-pair F4 gate. -/
def f4 {F : Type} [CommRing F] (a b c z : F) : F :=
  let ab := a*b
  let cz := c*z
  let A := 1+ab*ab
  let B := ab
  let C := a*a+b*b
  let D := 1+cz*cz
  let E := cz
  let G := c*c+z*z
  (A*G+C*D)*(A*G+C*D) + (A*E+B*D)*(B*G+C*E)

theorem f4_swap {F : Type} [CommRing F] (a b c z : F) :
    f4 a b c z = f4 b a c z := by
  dsimp [f4]
  grind +ring

/-- Equal-rotation source constraints and the F4 gate survive exchange. -/
theorem exchange_preserves_gate {F : Type} [CommRing F]
    (source : F → Prop) (a b c z : F)
    (ha : source a) (hb : source b) (hg : f4 a b c z = 0) :
    source b ∧ source a ∧ f4 b a c z = 0 := by
  exact ⟨hb, ha, (f4_swap a b c z).symm ▸ hg⟩

/-- Distinct code labels have exactly one increasing orientation. -/
theorem ordered_orientation (code0 code1 : Nat) (hneq : code0 ≠ code1) :
    code0 < code1 ∨ code1 < code0 := by
  omega

#print axioms OrderSymmetry.f4_swap
#print axioms OrderSymmetry.exchange_preserves_gate
#print axioms OrderSymmetry.ordered_orientation

end OrderSymmetry
