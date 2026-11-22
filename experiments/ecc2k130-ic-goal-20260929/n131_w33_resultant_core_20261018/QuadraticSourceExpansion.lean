import Std
import Init.Grind.Ring.Basic

namespace QuadraticSourceExpansion
open Lean.Grind

def boolWeights {F : Type} [CommRing F] : List (F × F) → Prop
  | [] => True
  | (b, _) :: xs => b*b = b ∧ boolWeights xs

def weightedSum {F : Type} [CommRing F] : List (F × F) → F
  | [] => 0
  | (b, a) :: xs => b*a + weightedSum xs

def weightedSquares {F : Type} [CommRing F] : List (F × F) → F
  | [] => 0
  | (b, a) :: xs => b*a*a + weightedSquares xs

def weightedCubeExpansion {F : Type} [CommRing F] : List (F × F) → F
  | [] => 0
  | (b, a) :: xs =>
      b*a*a*a + weightedCubeExpansion xs +
      b*a*a*weightedSum xs + b*a*weightedSquares xs

/-- Squaring a linear combination of Boolean coefficients is linear in
the coefficients in characteristic two. -/
theorem weighted_square {F : Type} [CommRing F] (h2 : (2 : F) = 0)
    (xs : List (F × F)) (hb : boolWeights xs) :
    (weightedSum xs)^2 = weightedSquares xs := by
  induction xs with
  | nil => simp only [weightedSum, weightedSquares]; grind +ring
  | cons pair tail ih =>
      rcases pair with ⟨b, a⟩
      simp only [boolWeights] at hb
      obtain ⟨hbool, htail⟩ := hb
      have hs := ih htail
      simp only [weightedSum, weightedSquares]
      grind +ring

/-- The cube of a linear combination of Boolean coefficients has only
singleton and pair terms in characteristic two. -/
theorem weighted_cube {F : Type} [CommRing F] (h2 : (2 : F) = 0)
    (xs : List (F × F)) (hb : boolWeights xs) :
    (weightedSum xs)^3 = weightedCubeExpansion xs := by
  induction xs with
  | nil => simp only [weightedSum, weightedCubeExpansion]; grind +ring
  | cons pair tail ih =>
      rcases pair with ⟨b, a⟩
      simp only [boolWeights] at hb
      obtain ⟨hbool, htail⟩ := hb
      have hs := weighted_square h2 tail htail
      have hc := ih htail
      simp only [weightedSum, weightedCubeExpansion]
      grind +ring

#print axioms weighted_square
#print axioms weighted_cube

end QuadraticSourceExpansion
