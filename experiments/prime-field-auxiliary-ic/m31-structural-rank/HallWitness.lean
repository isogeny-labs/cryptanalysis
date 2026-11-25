import Mathlib.LinearAlgebra.Dimension.Constructions
import Mathlib.LinearAlgebra.Dimension.Finite

namespace M31HallWitness

/-- If a row subset has fewer neighboring columns than rows, extending
its coefficient vectors back to the full column space preserves dependence. -/
theorem dependent {K I J V : Type*} [Field K] [Fintype I] [Fintype J]
    [AddCommGroup V] [Module K V] (rows : I → J → K) (extend : (J → K) →ₗ[K] V)
    (excess : Fintype.card J < Fintype.card I) :
    ¬ LinearIndependent K (extend ∘ rows) := by
  intro h
  have bound := (LinearIndependent.of_comp extend h).fintype_card_le_finrank
  rw [Module.finrank_pi] at bound
  exact (Nat.not_lt_of_ge bound) excess

#print axioms dependent
end M31HallWitness
