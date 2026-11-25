import Mathlib

namespace M31SingletonPeeling

variable {I C K : Type*} [DecidableEq I] [Field K]

/-- Read the constructor sequence backwards to peel one row at a time. -/
inductive Peelable (a : I → C → K) : Finset I → Prop where
  | empty : Peelable a ∅
  | step {s : Finset I} {i : I} (fresh : i ∉ s) (c : C) (pivot : a i c ≠ 0)
      (zeros : ∀ j ∈ s, a j c = 0) (rest : Peelable a s) : Peelable a (insert i s)

/-- Any vanishing linear combination of completely peelable rows is trivial. -/
theorem trivial_weights {a : I → C → K} {s : Finset I} (cert : Peelable a s)
    (w : I → K) (relation : ∀ c, ∑ i ∈ s, w i * a i c = 0) :
    ∀ i ∈ s, w i = 0 := by
  induction cert with
  | empty => simp
  | @step s i fresh c pivot zeros rest ih =>
    have h := relation c
    rw [Finset.sum_insert fresh, Finset.sum_eq_zero (fun j hj => by rw [zeros j hj, mul_zero]),
      add_zero] at h
    have wi := (mul_eq_zero.mp h).resolve_right pivot
    have remaining : ∀ t, ∑ j ∈ s, w j * a j t = 0 := by
      intro t
      simpa [Finset.sum_insert fresh, wi] using relation t
    intro j hj
    rcases Finset.mem_insert.mp hj with rfl | hj
    · exact wi
    · exact ih remaining j hj

end M31SingletonPeeling
