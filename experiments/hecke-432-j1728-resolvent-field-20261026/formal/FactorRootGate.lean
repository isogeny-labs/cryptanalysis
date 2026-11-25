import Mathlib.Algebra.Polynomial.Eval.Defs

namespace J1728ResolventField

open Polynomial

/-- The structural bridge from an exact quartic-octic factorization to a
    finite-field root test. The separate coefficient certificate establishes
    the factorization for the specialized Hecke resolvent. -/
theorem root_lies_in_quartic_or_octic
    {F : Type*} [Field F]
    (resolvent quartic octic : F[X]) (unit : F) (unit_ne_zero : unit ≠ 0)
    (factorization : resolvent = C unit * quartic * octic)
    (x : F) (root : resolvent.eval x = 0) :
    quartic.eval x = 0 ∨ octic.eval x = 0 := by
  rw [factorization, eval_mul, eval_mul, eval_C] at root
  rcases mul_eq_zero.mp root with h | h
  · rcases mul_eq_zero.mp h with hu | hq
    · exact False.elim (unit_ne_zero hu)
    · exact Or.inl hq
  · exact Or.inr h

#print axioms root_lies_in_quartic_or_octic

end J1728ResolventField
