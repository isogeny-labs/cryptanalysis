module

public import Mathlib.Algebra.Group.Hom.Defs
public import Mathlib.Tactic.Abel

/-! The inert-2 commutator constrains the sum of three descendant rows.
The concrete X₀(11) incidence and operator commutation are separately checked
in the saved finite-field experiment. -/
namespace ThreeDescendants

public def residualTwo {A : Type*} [AddCommGroup A] (T : A →+ A) (x : A) : A :=
  T x + 2 • x

public def residualThree {A : Type*} [AddCommGroup A] (T : A →+ A) (x : A) : A :=
  T x + x

public theorem three_downward_commutator {A : Type*} [AddCommGroup A]
    (T2 T3 : A →+ A) (hcomm : ∀ x, T2 (T3 x) = T3 (T2 x))
    (x q₁ q₂ q₃ w₁ w₂ w₃ w₄ : A)
    (h2 : T2 x = q₁ + q₂ + q₃)
    (h3 : T3 x = w₁ + w₂ + w₃ + w₄) :
    residualThree T3 q₁ + residualThree T3 q₂ + residualThree T3 q₃ =
      residualTwo T2 w₁ + residualTwo T2 w₂ +
      residualTwo T2 w₃ + residualTwo T2 w₄ +
      residualTwo T2 x - 2 • residualThree T3 x := by
  have hT : T2 w₁ + T2 w₂ + T2 w₃ + T2 w₄ =
      T3 q₁ + T3 q₂ + T3 q₃ := by
    calc
      _ = T2 (T3 x) := by rw [h3]; simp only [map_add]
      _ = T3 (T2 x) := hcomm x
      _ = _ := by rw [h2]; simp only [map_add]
  have hw : w₁ + w₂ + w₃ + w₄ = T3 x := h3.symm
  dsimp [residualTwo, residualThree]
  calc
    (T3 q₁ + q₁) + (T3 q₂ + q₂) + (T3 q₃ + q₃) =
        (T2 w₁ + T2 w₂ + T2 w₃ + T2 w₄) +
        2 • (w₁ + w₂ + w₃ + w₄) + T2 x + 2 • x -
        2 • (T3 x + x) := by
          rw [hT, hw, h2]
          abel
    _ = _ := by abel

end ThreeDescendants

#print axioms ThreeDescendants.three_downward_commutator
