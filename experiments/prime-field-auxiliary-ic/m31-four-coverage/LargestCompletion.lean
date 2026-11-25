import Mathlib.Data.Finset.Max
import Mathlib.Data.Finset.Card

namespace M31FourCoverage

/-- For a five-element support there is exactly one choice of the last
label which exceeds all four retained labels. -/
theorem unique_last {α : Type*} [LinearOrder α] (s : Finset α) (h : s.card = 5) :
    ∃! a, a ∈ s ∧ (s.erase a).card = 4 ∧ ∀ b ∈ s.erase a, b < a := by
  have hn : s.Nonempty := Finset.card_pos.mp (by omega)
  let m := s.max' hn
  have hm : m ∈ s := s.max'_mem hn
  refine ⟨m, ⟨hm, ?_, fun _ hb => s.lt_max'_of_mem_erase_max' hn hb⟩, ?_⟩
  · rw [Finset.card_erase_of_mem hm, h]
  · intro a ha
    by_contra hne
    have hlt := ha.2.2 m (Finset.mem_erase.mpr ⟨Ne.symm hne, hm⟩)
    exact (not_lt_of_ge (s.le_max' a ha.1)) hlt

end M31FourCoverage
