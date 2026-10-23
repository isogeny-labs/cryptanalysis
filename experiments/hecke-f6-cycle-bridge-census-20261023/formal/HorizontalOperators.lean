module

public import Mathlib.Tactic.Linarith
public import Mathlib.Algebra.Ring.Rat

/-! Rational kernels of the inert and ramified local horizontal operators. -/
namespace HorizontalOperators

public def inertOperator (x : ℚ) : ℚ := x

public theorem inert_kernel_trivial (x : ℚ) :
    inertOperator x = 0 ↔ x = 0 := by
  rfl

public def ramifiedOperator (x y : ℚ) : ℚ × ℚ := (x + y, y + x)

public theorem ramified_pair_kernel (x y : ℚ) :
    ramifiedOperator x y = (0, 0) ↔ ∃! t : ℚ, x = t ∧ y = -t := by
  constructor
  · intro h
    have hsum : x + y = 0 := congrArg Prod.fst h
    refine ⟨x, ?_, ?_⟩
    · constructor
      · rfl
      · linarith
    · intro t ht
      exact ht.1.symm
  · rintro ⟨t, ⟨rfl, hy⟩, -⟩
    simp [ramifiedOperator, hy]

public theorem ramified_pair_nonzero (t : ℚ) (ht : t ≠ 0) :
    ramifiedOperator t (-t) = (0, 0) ∧ (t, -t) ≠ ((0 : ℚ), 0) := by
  constructor
  · simp [ramifiedOperator]
  · intro h
    exact ht (congrArg Prod.fst h)

end HorizontalOperators

#print axioms HorizontalOperators.inert_kernel_trivial
#print axioms HorizontalOperators.ramified_pair_kernel
#print axioms HorizontalOperators.ramified_pair_nonzero
