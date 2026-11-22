import Std
import Init.Grind.Ring.Basic

namespace LazySourceCuts
open Lean.Grind

/-- The checked source policy: each slot uses a permitted pair code and no
    two distinct slots use the same folded factor-base column. -/
def Eligible {Code Column : Type} (codes : Fin 5 → Code)
    (allowed : Code → Prop) (uses : Code → Column → Prop) : Prop :=
  (∀ i, allowed (codes i)) ∧
  (∀ i j, i ≠ j → ¬ ∃ column, uses (codes i) column ∧ uses (codes j) column)

/-- A single invalid code can be excluded at its slot without excluding an
    eligible assignment. The code-to-source census supplies `not_allowed`. -/
theorem invalid_code_cut {Code Column : Type} (codes : Fin 5 → Code)
    (allowed : Code → Prop) (uses : Code → Column → Prop)
    (slot : Fin 5) (bad : Code)
    (valid : Eligible codes allowed uses) (not_allowed : ¬ allowed bad) :
    codes slot ≠ bad := by
  intro equal
  apply not_allowed
  rw [← equal]
  exact valid.1 slot

/-- When two fixed codes share a folded column, their joint assignment can
    be excluded without excluding an eligible assignment. -/
theorem collision_cut {Code Column : Type} (codes : Fin 5 → Code)
    (allowed : Code → Prop) (uses : Code → Column → Prop)
    (left right : Fin 5) (a b : Code) (column : Column)
    (distinct : left ≠ right)
    (a_uses : uses a column) (b_uses : uses b column)
    (valid : Eligible codes allowed uses) :
    codes left ≠ a ∨ codes right ≠ b := by
  classical
  by_cases hl : codes left = a
  · right
    intro hr
    have overlap : ∃ c, uses (codes left) c ∧ uses (codes right) c := by
      refine ⟨column, ?_, ?_⟩
      · rw [hl]
        exact a_uses
      · rw [hr]
        exact b_uses
    exact (valid.2 left right distinct) overlap
  · left
    exact hl

/-- The target-conditioned two-pair lookup preserves each exact five-point
    witness. The stored key is `left₀ + left₁`; the streamed key is formed
    from the target, the right pair, and the middle point. -/
theorem two_one_two_lookup {G : Type} [AddCommGroup G]
    (left₀ left₁ middle right₀ right₁ target : G) :
    ((((left₀ + left₁) + middle) + right₀) + right₁ = target) ↔
      (left₀ + left₁ = (target - (right₀ + right₁)) - middle) := by
  constructor
  · intro hit
    have h : (left₀ + left₁) + middle + (right₀ + right₁) = target := by
      calc
        (left₀ + left₁) + middle + (right₀ + right₁) =
            ((((left₀ + left₁) + middle) + right₀) + right₁) := by
              exact (AddCommMonoid.add_assoc _ _ _).symm
        _ = target := hit
    have h₁ : (left₀ + left₁) + middle = target - (right₀ + right₁) := by
      calc
        (left₀ + left₁) + middle =
            (((left₀ + left₁) + middle) + (right₀ + right₁)) -
              (right₀ + right₁) := AddCommGroup.add_sub_cancel.symm
        _ = target - (right₀ + right₁) := by rw [h]
    calc
      left₀ + left₁ = ((left₀ + left₁) + middle) - middle :=
        AddCommGroup.add_sub_cancel.symm
      _ = (target - (right₀ + right₁)) - middle := by rw [h₁]
  · intro lookup
    calc
      ((((left₀ + left₁) + middle) + right₀) + right₁) =
          ((left₀ + left₁) + middle) + (right₀ + right₁) := by
            exact AddCommMonoid.add_assoc _ _ _
      _ = ((target - (right₀ + right₁)) - middle + middle) +
            (right₀ + right₁) := by rw [lookup]
      _ = target := by
        calc
          ((target - (right₀ + right₁)) - middle + middle) + (right₀ + right₁) =
              (target - (right₀ + right₁)) + (right₀ + right₁) := by
                exact congrArg (fun x => x + (right₀ + right₁))
                  (AddCommGroup.sub_add_cancel)
          _ = target := AddCommGroup.sub_add_cancel

#print axioms Eligible
#print axioms invalid_code_cut
#print axioms collision_cut
#print axioms two_one_two_lookup

end LazySourceCuts
