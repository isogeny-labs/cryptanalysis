import Mathlib

namespace M31FourCoverage.FiveClasses

/-- Each simple five-letter class has two signs and 5! orders.
The encoding and measured cardinality are explicit hypotheses. -/
theorem count_classes {W C : Type*} [Fintype W] [Fintype C]
    (encoding : W ≃ C × Bool × Equiv.Perm (Fin 5))
    (measured : Fintype.card W = 4800) : Fintype.card C = 20 := by
  have h := Fintype.card_congr encoding
  rw [measured] at h
  simp [Fintype.card_perm, Nat.factorial] at h
  omega

/-- A sign representative per class suffices for a rank upper bound. -/
theorem span_bound {K V : Type*} [Field K] [AddCommGroup V] [Module K V]
    (s : Finset V) (measured : s.card ≤ 20) :
    Module.finrank K (Submodule.span K (s : Set V)) ≤ 20 :=
  (finrank_span_finset_le_card s).trans measured

end M31FourCoverage.FiveClasses
