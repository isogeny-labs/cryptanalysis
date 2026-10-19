import Std
import Init.Grind.Ring.Basic

namespace SourceProductLinear
open Lean.Grind

/-- The fixed-seed source product is additive in characteristic two. -/
theorem source_product_additive {R : Type} [CommRing R]
    (charTwo : (1 : R) + 1 = 0) (seed a b : R) :
    (a + b) * (a + b) + seed * (a + b) =
      (a * a + seed * a) + (b * b + seed * b) := by
  grind

/-- Repeated squaring, the field operation used for the Frobenius rotation. -/
def frobIter {R : Type} [CommRing R] : Nat → R → R
  | 0, x => x
  | k + 1, x => let y := frobIter k x; y * y

theorem frobIter_additive {R : Type} [CommRing R]
    (charTwo : (1 : R) + 1 = 0) (k : Nat) (a b : R) :
    frobIter k (a + b) = frobIter k a + frobIter k b := by
  induction k with
  | zero => rfl
  | succ k ih => grind [frobIter]

/-- A prefix/suffix factorization of an invertible batch product supplies
    the inverse certificate for one factor. -/
theorem batch_inverse_sound {R : Type} [CommRing R]
    (a pref suff : R) (wholeInverse : (pref * a) * suff = 1) :
    a * (pref * suff) = 1 := by
  grind

#print axioms source_product_additive
#print axioms frobIter_additive
#print axioms batch_inverse_sound
end SourceProductLinear
