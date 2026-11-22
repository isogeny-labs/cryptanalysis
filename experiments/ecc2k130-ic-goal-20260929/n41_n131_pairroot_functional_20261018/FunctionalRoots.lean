import Std
import Init.Grind.Ring.Basic

namespace FunctionalRoots
open Lean.Grind

/-- The source-pair equation after the change of variable `p*v = C*u`.
The nonzero coefficient assumptions give the reverse implication. -/
theorem source_normalization
    {F : Type} [Field F] (charTwo : ∀ x : F, x+x=0)
    (C p H u v : F) (hC : C ≠ 0)
    (hlink : p*v=C*u) :
    (C*u*u+p*u+H=0 ↔ p*p*(v*v+v)+C*H=0) := by
  have htwo : (2 : F)=0 := by
    have hz := charTwo 1
    grind +ring
  have hsquare : p*p*v*v=C*C*u*u := by
    have hz := congrArg (fun z : F => z*z) hlink
    grind +ring
  have hid : p*p*(v*v+v)+C*H=C*(C*u*u+p*u+H) := by
    grind +ring
  constructor
  · intro hz
    rw [hid,hz]
    grind +ring
  · intro hz
    rw [hid] at hz
    grind

/-- The target-conditioned S3 quadratic after `B*r = A*w`. -/
theorem target_normalization
    {F : Type} [Field F] (charTwo : ∀ x : F, x+x=0)
    (A B D w r : F) (hA : A ≠ 0)
    (hlink : B*r=A*w) :
    (A*w*w+B*w+D=0 ↔ B*B*(r*r+r)+A*D=0) := by
  have htwo : (2 : F)=0 := by
    have hz := charTwo 1
    grind +ring
  have hsquare : B*B*r*r=A*A*w*w := by
    have hz := congrArg (fun z : F => z*z) hlink
    grind +ring
  have hid : B*B*(r*r+r)+A*D=A*(A*w*w+B*w+D) := by
    grind +ring
  constructor
  · intro hz
    rw [hid,hz]
    grind +ring
  · intro hz
    rw [hid] at hz
    grind

/-- In characteristic two, any two roots of an Artin-Schreier equation
differ by zero or one. This is the exact two-branch completeness step. -/
theorem two_branch_completeness
    {F : Type} [Field F] (charTwo : ∀ x : F, x+x=0)
    (q h v : F) (hh : h*h+h=q) (hv : v*v+v=q) :
    v=h ∨ v=h+1 := by
  have htwo : (2 : F)=0 := by
    have hz := charTwo 1
    grind +ring
  have hf : (v+h)*(v+h+1)=0 := by
    grind +ring
  have hz : v+h=0 ∨ v+h+1=0 := by grind
  rcases hz with hzero | hone
  · left
    grind +ring
  · right
    grind +ring

#print axioms FunctionalRoots.source_normalization
#print axioms FunctionalRoots.target_normalization
#print axioms FunctionalRoots.two_branch_completeness

end FunctionalRoots
