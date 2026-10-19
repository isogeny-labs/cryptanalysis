import Std
import Init.Grind.Ring.Basic

namespace FoldedCollision
open Lean.Grind

def frob {F : Type} [Field F] : Nat → F → F
  | 0, x => x
  | n+1, x => frob n x * frob n x

/-- Frobenius powers preserve addition in characteristic two. -/
theorem frob_add {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0) (k : Nat) (a b : F) :
    frob k (a+b)=frob k a+frob k b := by
  induction k with
  | zero => rfl
  | succ k ih =>
    have htwo : (2 : F)=0 := by
      have hz:=charTwo 1
      grind +ring
    simp only [frob, ih]
    grind +ring

/-- Each folded endpoint equality is an affine equation in the two
source parameters after its fixed seed offset is moved to the right. -/
theorem collision_linearized {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0) (k : Nat)
    (a b e f seed : F) :
    frob k (a+e*seed)=b+f*seed ↔
    frob k a+b=frob k (e*seed)+f*seed := by
  rw [frob_add charTwo]
  have htwo : (2 : F)=0 := by
    have hz:=charTwo 1
    grind +ring
  grind +ring

#print axioms FoldedCollision.frob_add
#print axioms FoldedCollision.collision_linearized

end FoldedCollision
