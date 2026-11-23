import Mathlib

namespace M31SmoothDirectory

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
