import Mathlib.Tactic

namespace M31PackedFiber

/-- Both siblings have the same image under the rational map evaluated by the fold. -/
theorem sibling_image {K : Type*} [Field K] (u v a b : K)
    (prod : u * v = b) (nonzero : b ≠ 0) :
    u + a + b/u = u + a + v ∧ v + a + b/v = u + a + v := by
  have hu : u ≠ 0 := fun h => nonzero (by simp [← prod, h])
  have hv : v ≠ 0 := fun h => nonzero (by simp [← prod, h])
  subst b
  constructor
  · field_simp
  · field_simp
    ring

/-- An address is extended by one sibling choice at each level. -/
def Address : Nat → Type
  | 0 => Unit
  | d+1 => Address d × Bool

theorem injective_levels {X : Type*} (nodes : (d : Nat) → Address d → X)
    (step : Nat → X → X) (depth : Nat)
    (fold : ∀ d < depth, ∀ i b, step d (nodes (d+1) (i,b)) = nodes d i)
    (distinct : ∀ d < depth, ∀ i, nodes (d+1) (i,false) ≠ nodes (d+1) (i,true)) :
    ∀ d ≤ depth, Function.Injective (nodes d) := by
  intro d
  induction d with
  | zero => intro _ a b _; cases a; cases b; rfl
  | succ d ih =>
    intro hd
    have lt : d < depth := hd
    rintro ⟨i,b⟩ ⟨j,c⟩ he
    have eq := ih (Nat.le_of_lt lt) ((fold d lt i b).symm.trans ((congrArg (step d) he).trans (fold d lt j c)))
    subst j
    cases b <;> cases c
    · rfl
    · exact (distinct d lt i he).elim
    · exact (distinct d lt i he.symm).elim
    · rfl

end M31PackedFiber
