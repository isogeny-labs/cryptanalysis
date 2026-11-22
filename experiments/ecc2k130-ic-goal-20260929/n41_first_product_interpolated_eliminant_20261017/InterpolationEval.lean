import Std
import Init.Grind.Ring.Basic

namespace InterpolationEval
open Lean.Grind

/-- Evaluate the first `n` coefficients of a polynomial in ascending order. -/
def evalPrefix {R : Type} [CommRing R] : Nat → (Nat → R) → R → R
  | 0, _, _ => 0
  | n + 1, coeff, x => evalPrefix n coeff x + coeff n * x ^ n

/-- Evaluation is additive in the coefficient vector. -/
theorem evalPrefix_add {R : Type} [CommRing R]
    (n : Nat) (a b : Nat → R) (x : R) :
    evalPrefix n (fun i => a i + b i) x =
      evalPrefix n a x + evalPrefix n b x := by
  induction n with
  | zero => grind [evalPrefix]
  | succ n ih =>
      simp only [evalPrefix, ih]
      grind

/-- Evaluation commutes with scaling all coefficients by one field element. -/
theorem evalPrefix_smul {R : Type} [CommRing R]
    (n : Nat) (c : R) (a : Nat → R) (x : R) :
    evalPrefix n (fun i => c * a i) x = c * evalPrefix n a x := by
  induction n with
  | zero => grind [evalPrefix]
  | succ n ih =>
      simp only [evalPrefix, ih]
      grind

#print axioms evalPrefix_add
#print axioms evalPrefix_smul

end InterpolationEval
