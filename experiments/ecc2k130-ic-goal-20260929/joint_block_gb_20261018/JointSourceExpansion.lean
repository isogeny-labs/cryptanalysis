import Std
import Init.Grind.Ring.Basic

namespace JointSourceExpansion
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

def weightedCubes {F : Type} [CommRing F] : List (F × F) → F
  | [] => 0
  | (b, a) :: xs =>
      b*a*a*a + weightedCubes xs +
      b*a*a*weightedSum xs + b*a*weightedSquares xs

def weightedFourths {F : Type} [CommRing F] : List (F × F) → F
  | [] => 0
  | (b, a) :: xs => b*a*a*a*a + weightedFourths xs

/-- Binary squaring preserves linearity in Boolean coefficients. -/
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

/-- Binary cubing uses only singleton and pair products of the coefficients. -/
theorem weighted_cube {F : Type} [CommRing F] (h2 : (2 : F) = 0)
    (xs : List (F × F)) (hb : boolWeights xs) :
    (weightedSum xs)^3 = weightedCubes xs := by
  induction xs with
  | nil => simp only [weightedSum, weightedCubes]; grind +ring
  | cons pair tail ih =>
      rcases pair with ⟨b, a⟩
      simp only [boolWeights] at hb
      obtain ⟨hbool, htail⟩ := hb
      have hs := weighted_square h2 tail htail
      have hc := ih htail
      simp only [weightedSum, weightedCubes]
      grind +ring

/-- Fourth powers return to a linear expression in Boolean coefficients. -/
theorem weighted_fourth {F : Type} [CommRing F] (h2 : (2 : F) = 0)
    (xs : List (F × F)) (hb : boolWeights xs) :
    (weightedSum xs)^4 = weightedFourths xs := by
  induction xs with
  | nil => simp only [weightedSum, weightedFourths]; grind +ring
  | cons pair tail ih =>
      rcases pair with ⟨b, a⟩
      simp only [boolWeights] at hb
      obtain ⟨hbool, htail⟩ := hb
      have hf := ih htail
      simp only [weightedSum, weightedFourths]
      grind +ring

/-- The cubic-by-cubic term of the two-source resultant has the
explicit product of the two source-pair expansions. -/
theorem joint_cubic_rewrite {F : Type} [CommRing F] (h2 : (2 : F) = 0)
    (ps qs : List (F × F)) (hp : boolWeights ps) (hq : boolWeights qs) :
    (weightedSum ps)^3 * (weightedSum qs)^3 =
      weightedCubes ps * weightedCubes qs := by
  rw [weighted_cube h2 ps hp, weighted_cube h2 qs hq]

def supportedExponent (e : Nat) : Prop :=
  e = 0 ∨ e = 1 ∨ e = 2 ∨ e = 3 ∨ e = 4

def expandedPower {F : Type} [CommRing F] (e : Nat) (xs : List (F × F)) : F :=
  if e = 0 then 1
  else if e = 1 then weightedSum xs
  else if e = 2 then weightedSquares xs
  else if e = 3 then weightedCubes xs
  else if e = 4 then weightedFourths xs
  else 0

theorem source_power_correct {F : Type} [CommRing F] (h2 : (2 : F) = 0)
    (xs : List (F × F)) (hb : boolWeights xs) (e : Nat)
    (he : supportedExponent e) :
    (weightedSum xs)^e = expandedPower e xs := by
  rcases he with h | h | h | h | h
  · subst e
    change (weightedSum xs)^0 = (1 : F)
    grind +ring
  · subst e
    change (weightedSum xs)^1 = weightedSum xs
    grind +ring
  · subst e; simpa [expandedPower] using weighted_square h2 xs hb
  · subst e; simpa [expandedPower] using weighted_cube h2 xs hb
  · subst e; simpa [expandedPower] using weighted_fourth h2 xs hb

def supportedTerms {F : Type} : List (Nat × Nat × F) → Prop
  | [] => True
  | (i, j, _) :: tail =>
      supportedExponent i ∧ supportedExponent j ∧ supportedTerms tail

def evalTerms {F : Type} [CommRing F] (p q : F) : List (Nat × Nat × F) → F
  | [] => 0
  | (i, j, c) :: tail => c * p^i * q^j + evalTerms p q tail

def expandedTerms {F : Type} [CommRing F]
    (ps qs : List (F × F)) : List (Nat × Nat × F) → F
  | [] => 0
  | (i, j, c) :: tail =>
      c * expandedPower i ps * expandedPower j qs +
      expandedTerms ps qs tail

/-- A target polynomial with exponents at most four in each source
product equals its exact joint Boolean-source expansion. -/
theorem joint_resultant_expansion {F : Type} [CommRing F] (h2 : (2 : F) = 0)
    (ps qs : List (F × F)) (hp : boolWeights ps) (hq : boolWeights qs)
    (terms : List (Nat × Nat × F)) (ht : supportedTerms terms) :
    evalTerms (weightedSum ps) (weightedSum qs) terms =
      expandedTerms ps qs terms := by
  induction terms with
  | nil => rfl
  | cons term tail ih =>
      rcases term with ⟨i, j, c⟩
      simp only [supportedTerms] at ht
      obtain ⟨hi, hj, htail⟩ := ht
      simp only [evalTerms, expandedTerms]
      rw [source_power_correct h2 ps hp i hi,
          source_power_correct h2 qs hq j hj, ih htail]

#print axioms weighted_square
#print axioms weighted_cube
#print axioms weighted_fourth
#print axioms joint_cubic_rewrite
#print axioms source_power_correct
#print axioms joint_resultant_expansion

end JointSourceExpansion
