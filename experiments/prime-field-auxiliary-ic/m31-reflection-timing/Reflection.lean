import Mathlib.Tactic.Ring

/-- Reflecting the coordinate around zero preserves the constant part of both
target evaluations and negates their common odd part. -/
theorem reflection_evaluation {R : Type*} [CommRing R] (a b x : R) :
    (-x)^3 + a*(-x) + b = b - (x^3+a*x) := by ring
