import Std.Tactic
import Init.Grind.Ring.Basic
set_option autoImplicit false

namespace LPGraphCases02
open Lean.Grind

/-- Scalar relations for the exact four-edge synthetic raw graph. The final
edge contains two occurrences of the first factor-base variable. -/
def EvenFour {K : Type} [CommRing K]
    (f g eta a b c d : K) : Prop :=
  a + b + f - eta = 0 ∧
  b + c + g - eta = 0 ∧
  c + d + f - eta = 0 ∧
  d + a + (f + f) - eta = 0

def Triangle {K : Type} [CommRing K]
    (f eta a b c : K) : Prop :=
  a + b + f - eta = 0 ∧
  b + c + f - eta = 0 ∧
  c + a + f - eta = 0

/-- Complete elimination with an explicit lift; no span/completeness premise. -/
theorem even_four_projection_iff {K : Type} [CommRing K]
    (f g eta : K) :
    (∃ a b c d, EvenFour f g eta a b c d) ↔ g = 0 := by
  constructor
  · rintro ⟨a, b, c, d, h⟩
    grind [EvenFour]
  · intro h
    refine ⟨0, eta - f, f, eta - (f + f), ?_⟩
    grind [EvenFour]

/-- A lone odd cycle has no factor-base constraint when two is invertible.
The inverse-of-two hypothesis is explicit; there is no characteristic-two
claim and no specialization to a numerical field in this module. -/
theorem triangle_has_lift {K : Type} [CommRing K]
    (half : K) (two_half : (2 : K) * half = 1) (f eta : K) :
    ∃ a b c, Triangle f eta a b c := by
  refine ⟨half * (eta - f), half * (eta - f), half * (eta - f), ?_⟩
  grind [Triangle]

/-- Two odd cycles based at the same unknown LP variable impose equality of
their factor-base terms. The backward implication constructs a full lift. -/
theorem shared_odd_projection_iff {K : Type} [CommRing K]
    (half : K) (two_half : (2 : K) * half = 1) (f g eta : K) :
    (∃ a b c d e, Triangle f eta a b c ∧ Triangle g eta a d e) ↔ f = g := by
  constructor
  · rintro ⟨a, b, c, d, e, hf, hg⟩
    grind [Triangle]
  · intro h
    subst g
    obtain ⟨a, b, c, ha⟩ := triangle_has_lift half two_half f eta
    exact ⟨a, b, c, b, c, ha, ha⟩

/-- Distinct odd-cycle roots are independent nuisance variables. -/
theorem disconnected_odd_has_lifts {K : Type} [CommRing K]
    (half : K) (two_half : (2 : K) * half = 1) (f g eta : K) :
    ∃ a b c d e z, Triangle f eta a b c ∧ Triangle g eta d e z := by
  obtain ⟨a, b, c, ha⟩ := triangle_has_lift half two_half f eta
  obtain ⟨d, e, z, hb⟩ := triangle_has_lift half two_half g eta
  exact ⟨a, b, c, d, e, z, ha, hb⟩

/-- The synthetic ordinary ground fixes its LP variable to eta. -/
theorem grounded_triangle_projection_iff {K : Type} [CommRing K]
    (f eta : K) :
    (∃ a b c, a = eta ∧ Triangle f eta a b c) ↔ eta + f = 0 := by
  constructor
  · rintro ⟨a, b, c, hground, htriangle⟩
    grind [Triangle]
  · intro h
    refine ⟨eta, -f, eta, rfl, ?_⟩
    grind [Triangle]

/-- A half ground plus one new tree endpoint still has no FB constraint. -/
theorem half_ground_edge_has_lift {K : Type} [CommRing K]
    (half : K) (two_half : (2 : K) * half = 1) (f g eta : K) :
    ∃ a b, 2 * a + (f + f) - eta = 0 ∧ a + b + f + g - eta = 0 := by
  let a := half * (eta - (f + f))
  refine ⟨a, eta - f - g - a, ?_⟩
  dsimp [a]
  grind

/-- An explicit excluded projected vector in every nonzero ring. This is a
scalar relation-system statement, not a theorem about the original program,
geometric point membership, subgroup logs, or a computational advantage. -/
theorem even_four_no_unit_lift {K : Type} [CommRing K]
    (one_ne_zero : (1 : K) ≠ 0) :
    ¬ ∃ a b c d, EvenFour (0 : K) 1 0 a b c d := by
  intro h
  exact one_ne_zero ((even_four_projection_iff (0 : K) 1 0).mp h)

end LPGraphCases02
