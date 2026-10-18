import Std
import Init.Grind.Ring.Basic

namespace SharedQuadratic
open Lean.Grind

/-- The only coefficient of the second-source cubic in the frozen
13-term support is c13*p + c33*p^3. -/
def leading {F : Type} [CommRing F] (c13 c33 p : F) : F :=
  p * (c13 + c33 * p^2)

theorem leading_expansion {F : Type} [CommRing F]
    (c13 c33 p : F) :
    leading c13 c33 p = c13*p + c33*p^3 := by
  unfold leading
  grind +ring

/-- Normalization preserves every zero whenever the leading
coefficient has the supplied reciprocal. -/
theorem normalized_zero_iff {F : Type} [CommRing F]
    (a reciprocal value : F) (hunit : a * reciprocal = 1) :
    (reciprocal * value = 0) ↔ (value = 0) := by
  constructor
  · intro h
    have hprod := congrArg (fun z : F => a * z) h
    grind +ring
  · intro h
    subst value
    grind +ring

/-- Every second-code quadratic coefficient becomes the same B_ij
after normalization; this is an identity for arbitrary source values. -/
theorem shared_quadratic_coefficient {F : Type} [CommRing F]
    (a reciprocal b : F) (hunit : a * reciprocal = 1) :
    reciprocal * (a * b) = b := by
  grind +ring

/-- The exceptional source values are precisely the roots of the two
displayed factors, under the stated no-zero-divisors hypothesis. -/
theorem exceptional_factorization {F : Type} [CommRing F]
    (c13 c33 p : F)
    (hzero : ∀ a b : F, a*b = 0 → a = 0 ∨ b = 0) :
    leading c13 c33 p = 0 ↔ p = 0 ∨ c13 + c33*p^2 = 0 := by
  constructor
  · intro h
    exact hzero p (c13 + c33*p^2) h
  · intro h
    rcases h with hp | hf
    · simp only [leading]; grind +ring
    · simp only [leading]; grind +ring

/-- The complete ordered two-source, sixteen-branch enumeration has
exactly sixteen entries per ordered code pair, before duplicates or
invalid source points are removed. -/
def branchEnumeration {A B P : Type}
    (first : List A) (second : List B)
    (emit : A → B → Fin 16 → P) : List P :=
  first.flatMap (fun a => second.flatMap
    (fun b => (List.finRange 16).map (emit a b)))

private theorem constant_sum {A : Type} (xs : List A) (n : Nat) :
    (xs.map (fun _ => n)).sum = n * xs.length := by
  induction xs with
  | nil => simp
  | cons _ tail ih =>
      simp only [List.map_cons, List.sum_cons, List.length_cons, ih]
      grind +ring

theorem branch_enumeration_length {A B P : Type}
    (first : List A) (second : List B)
    (emit : A → B → Fin 16 → P) :
    (branchEnumeration first second emit).length =
      16 * first.length * second.length := by
  simp only [branchEnumeration, List.length_flatMap, List.length_map,
    List.length_finRange]
  rw [constant_sum second 16]
  rw [constant_sum first (16 * second.length)]
  grind +ring

#print axioms leading_expansion
#print axioms normalized_zero_iff
#print axioms shared_quadratic_coefficient
#print axioms exceptional_factorization
#print axioms branch_enumeration_length

end SharedQuadratic
