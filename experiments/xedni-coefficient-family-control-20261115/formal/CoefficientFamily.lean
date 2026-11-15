import Mathlib

namespace XedniCoefficientFamily

/-- Two distinct projective coefficient directions can share a relation
only when both sampled point scalars vanish. -/
theorem distinct_directions_force_zero {F : Type*} [Field F]
    (a b c d x y : F) (hdet : a * d - b * c ≠ 0)
    (h₁ : a * x + b * y = 0) (h₂ : c * x + d * y = 0) :
    x = 0 ∧ y = 0 := by
  have hx : (a * d - b * c) * x = 0 := by
    linear_combination d * h₁ - b * h₂
  have hy : (a * d - b * c) * y = 0 := by
    linear_combination a * h₂ - c * h₁
  exact ⟨(mul_eq_zero.mp hx).resolve_left hdet,
    (mul_eq_zero.mp hy).resolve_left hdet⟩

/-- A vector with coefficient sum zero tests equality of the two sampled
scalars, so it cannot hit a distinct-point query. -/
theorem zero_sum_pair_relation {F : Type*} [Field F]
    (a x y : F) (ha : a ≠ 0) (hxy : x ≠ y) :
    a * x + (-a) * y ≠ 0 := by
  intro h
  have hdiff : a * (x - y) = 0 := by
    linear_combination h
  exact hxy ((mul_eq_zero.mp hdiff).resolve_left ha |> sub_eq_zero.mp)

#print axioms distinct_directions_force_zero
#print axioms zero_sum_pair_relation

end XedniCoefficientFamily
