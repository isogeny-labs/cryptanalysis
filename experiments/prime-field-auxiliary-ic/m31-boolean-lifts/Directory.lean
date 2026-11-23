import Mathlib

namespace M31SmoothDirectory

/-- Counting sorted keys below a bucket produces precisely its first index. -/
theorem countBoundary {n : ℕ} (key : Fin n → ℕ) (sorted : Monotone key)
    (i : Fin n) (b : ℕ) :
    i.val < (Finset.univ.filter (fun j => key j / 4096 < b)).card ↔ key i / 4096 < b := by
  constructor
  · intro h
    by_contra! hi
    have sub : Finset.univ.filter (fun j => key j / 4096 < b) ⊆ Finset.Iio i := by
      intro j hj
      simp only [Finset.mem_Iio]
      by_contra! hij
      have hle : key i / 4096 ≤ key j / 4096 := Nat.div_le_div_right (sorted hij)
      have := (Finset.mem_filter.mp hj).2
      omega
    have := Finset.card_le_card sub
    exact (not_lt_of_ge (show i.val ≥ _ by simpa using this)) h
  · intro h
    have sub : Finset.Iic i ⊆ Finset.univ.filter (fun j => key j / 4096 < b) := by
      intro j hj
      exact Finset.mem_filter.mpr ⟨Finset.mem_univ _, lt_of_le_of_lt
        (Nat.div_le_div_right (sorted (Finset.mem_Iic.mp hj))) h⟩
    have hc := Finset.card_le_card sub
    simpa [Nat.succ_le_iff] using hc

/-- When first[b] is the count of keys in buckets below b in a sorted
array, a key equal to q must occur between first[q/4096] and the next
offset. This also covers empty buckets and an upper index equal to n. -/
theorem exactRange {n : ℕ} (key : Fin n → ℕ) (first : ℕ → ℕ)
    (boundary : ∀ i b, i.val < first b ↔ key i / 4096 < b)
    (q : ℕ) :
    (∃ i, key i = q) ↔
    ∃ i, first (q/4096) ≤ i.val ∧ i.val < first (q/4096+1) ∧ key i = q := by
  constructor
  · rintro ⟨i, hi⟩
    refine ⟨i, ?_, ?_, hi⟩
    · exact Nat.le_of_not_gt (fun h => (Nat.lt_irrefl _ (hi ▸ (boundary i _).mp h)))
    · exact (boundary i _).mpr (by rw [hi]; omega)
  · rintro ⟨i, _, _, hi⟩
    exact ⟨i, hi⟩

theorem allocation (q : ℕ) (h : q < 2147483647) :
    q / 4096 + 1 < 524289 := by omega

end M31SmoothDirectory
