import Mathlib.Tactic

namespace SignedSmooth

theorem opposite {R : Type*} [CommRing R] (x : R) :
    ((-x)^3 + (-x) = -(x^3+x)) ∧
    ((-x)^3+2*(-x)+14 = 28-(x^3+2*x+14)) := by
  constructor <;> ring

theorem exclusive {K : Type*} [Field K] (v : K) (hv : v ≠ 0)
    (hn : ¬ IsSquare (-1 : K)) : ¬ (IsSquare v ∧ IsSquare (-v)) := by
  rintro ⟨⟨a, ha⟩, ⟨b, hb⟩⟩
  apply hn
  refine ⟨b/a, ?_⟩
  have h : a ≠ 0 := by
    intro hz
    simp [hz] at ha
    exact hv ha
  field_simp
  linear_combination hb + ha

end SignedSmooth
