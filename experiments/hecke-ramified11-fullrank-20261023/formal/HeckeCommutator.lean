module

public import Mathlib.Algebra.Group.Hom.Defs
public import Mathlib.Tactic.Abel

/-! Formal residual-operator identity behind the eight-term row witnesses.
The arithmetic Hecke operators commute; the saved finite-field rows supply
the concrete point-incidence hypotheses. -/
namespace HeckeCommutator

public def residualTwo {A : Type*} [AddCommGroup A]
    (T : A →+ A) (x : A) : A := T x + 2 • x

public def residualThree {A : Type*} [AddCommGroup A]
    (T : A →+ A) (x : A) : A := T x + x

public theorem residuals_commute {A : Type*} [AddCommGroup A]
    (T2 T3 : A →+ A) (hcomm : ∀ x, T2 (T3 x) = T3 (T2 x))
    (x : A) :
    residualTwo T2 (residualThree T3 x) =
      residualThree T3 (residualTwo T2 x) := by
  simp only [residualTwo, residualThree, map_add, map_nsmul]
  rw [hcomm]
  abel

public theorem isolate_unique_two_descendant {A : Type*} [AddCommGroup A]
    (T2 T3 : A →+ A) (hcomm : ∀ x, T2 (T3 x) = T3 (T2 x))
    (x q u v w₁ w₂ w₃ w₄ : A)
    (h2 : T2 x = q + u + v)
    (h3 : T3 x = w₁ + w₂ + w₃ + w₄) :
    residualThree T3 q =
      residualTwo T2 w₁ + residualTwo T2 w₂ +
      residualTwo T2 w₃ + residualTwo T2 w₄ +
      residualTwo T2 x - residualThree T3 u -
      residualThree T3 v - 2 • residualThree T3 x := by
  have hT : T2 w₁ + T2 w₂ + T2 w₃ + T2 w₄ =
      T3 q + T3 u + T3 v := by
    calc
      _ = T2 (T3 x) := by rw [h3]; simp only [map_add]
      _ = T3 (T2 x) := hcomm x
      _ = _ := by rw [h2]; simp only [map_add]
  have hw : w₁ + w₂ + w₃ + w₄ = T3 x := h3.symm
  dsimp [residualTwo, residualThree]
  calc
    T3 q + q =
        (T2 w₁ + T2 w₂ + T2 w₃ + T2 w₄) +
        2 • (w₁ + w₂ + w₃ + w₄) + T2 x + 2 • x -
        (T3 u + u) - (T3 v + v) - 2 • (T3 x + x) := by
          rw [hT, hw, h2]
          abel
    _ = _ := by abel

end HeckeCommutator

#print axioms HeckeCommutator.residuals_commute
#print axioms HeckeCommutator.isolate_unique_two_descendant
