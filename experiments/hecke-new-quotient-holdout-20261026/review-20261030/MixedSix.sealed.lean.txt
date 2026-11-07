module

public import Mathlib.Tactic.Linarith

/-! Conditional coefficient argument for six mixed floor-incidence components.
The equations are supplied by the integer certificate replay, not assumed to
hold for arbitrary Hecke matrices. -/
namespace MixedSix

/-- Two floor coordinates with opposite cycle/pair ratios force both
coefficients to vanish. -/
public theorem local_mixed_zero (cycle pair : ℚ)
    (positive_coordinate : cycle + pair = 0)
    (negative_coordinate : -cycle + pair = 0) :
    cycle = 0 ∧ pair = 0 := by
  constructor <;> linarith

/-- If each of six cycles meets each of its eight pair blocks in both
orientations, the 54 coefficients of a vanishing combination are zero. -/
public theorem six_by_eight_mixed_zero
    (cycle : Fin 6 → ℚ) (pair : Fin 6 → Fin 8 → ℚ)
    (positive_coordinates : ∀ i j, cycle i + pair i j = 0)
    (negative_coordinates : ∀ i j, -cycle i + pair i j = 0) :
    (∀ i, cycle i = 0) ∧ (∀ i j, pair i j = 0) := by
  constructor
  · intro i
    exact (local_mixed_zero (cycle i) (pair i 0)
      (positive_coordinates i 0) (negative_coordinates i 0)).1
  · intro i j
    exact (local_mixed_zero (cycle i) (pair i j)
      (positive_coordinates i j) (negative_coordinates i j)).2

end MixedSix

#print axioms MixedSix.local_mixed_zero
#print axioms MixedSix.six_by_eight_mixed_zero
