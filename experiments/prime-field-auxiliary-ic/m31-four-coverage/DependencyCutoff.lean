import Mathlib

namespace M31DependencyCutoff

variable {ι K : Type*} [Field K]

/-- A threshold admits a nonzero dependency when its excluded rows have zero weight. -/
def Admits (D : Submodule K (ι → K)) (cost : ι → ℕ) (b : ℕ) : Prop :=
  ∃ v ∈ D, v ≠ 0 ∧ ∀ i, b < cost i → v i = 0

/-- For a one-generator dependency space, the greatest cost on its generator's
support is the sharp threshold. The witness supplies attainment of the maximum. -/
theorem sharp {D : Submodule K (ι → K)} {w : ι → K} {cost : ι → ℕ}
    {cutoff b : ℕ} (hw : w ∈ D) (generates : ∀ v ∈ D, ∃ a : K, v = a • w)
    (upper : ∀ i, w i ≠ 0 → cost i ≤ cutoff)
    (attained : ∃ i, w i ≠ 0 ∧ cost i = cutoff) :
    Admits D cost b ↔ cutoff ≤ b := by
  obtain ⟨i, hi, hc⟩ := attained
  constructor
  · rintro ⟨v, hv, hn, hz⟩
    obtain ⟨a, rfl⟩ := generates v hv
    by_contra! h
    have ha : a ≠ 0 := fun h0 => hn (by simp [h0])
    have hp := hz i (hc.symm ▸ h)
    exact (mul_ne_zero ha hi) hp
  · intro h
    refine ⟨w, hw, ?_, ?_⟩
    · intro z
      exact hi (by simp [z])
    · intro j hj
      by_contra nz
      exact (Nat.not_lt_of_ge ((upper j nz).trans h)) hj

end M31DependencyCutoff
