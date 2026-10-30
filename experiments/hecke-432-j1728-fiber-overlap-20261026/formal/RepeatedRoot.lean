import Mathlib.Algebra.Polynomial.FieldDivision

open Polynomial

namespace J1728FiberOverlap

variable {K : Type*} [Field K] (f : K[X]) (a : K)

/-- A repeated root is exactly a common root of a polynomial and its derivative. -/
theorem repeated_root_iff_derivative_root (hf : f ≠ 0) :
    1 < f.rootMultiplicity a ↔ f.IsRoot a ∧ (derivative f).IsRoot a :=
  Polynomial.one_lt_rootMultiplicity_iff_isRoot hf

#print axioms repeated_root_iff_derivative_root

end J1728FiberOverlap
