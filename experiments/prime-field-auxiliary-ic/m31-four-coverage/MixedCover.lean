import PeriodicCover

namespace M31PeriodicCover
open M31TerminalSeparation M31ArchiveData

-- Any point may choose its own depth, including depth zero.
theorem minimum_mixed (targets : Finset Nat)
    (covers : ∀ q ∈ archived, ∃ n, label n q.1 ∈ targets) :
    11 ≤ targets.card := by
  classical
  let visits (q : Nat × Nat) (t : Nat) := q ∈ archived ∧ ∃ n, label n q.1 = t
  let back (t : Nat) := if h : ∃ q, visits q t then label 31 (Classical.choose h).1 else 0
  have sub : labels 31 ⊆ targets.image back := by
    intro t ht
    obtain ⟨q,hq,rfl⟩ := List.mem_map.mp (List.mem_toFinset.mp ht)
    obtain ⟨n,hn⟩ := covers q hq
    apply Finset.mem_image.mpr
    refine ⟨label n q.1,hn,?_⟩
    have seen : ∃ w, visits w (label n q.1) := ⟨q,hq,n,rfl⟩
    simp only [back, seen, ↓reduceDIte]
    obtain ⟨hw,i,hi⟩ := Classical.choose_spec seen
    exact variable_depth hw hq i n hi
  rw [← size31]
  exact (Finset.card_le_card sub).trans Finset.card_image_le

theorem attained_mixed : ∃ targets : Finset Nat, targets.card = 11 ∧
    ∀ q ∈ archived, ∃ n, label n q.1 ∈ targets := by
  refine ⟨labels 31,size31,?_⟩
  intro q hq
  exact ⟨31,List.mem_toFinset.mpr (List.mem_map.mpr ⟨q,hq,rfl⟩)⟩

end M31PeriodicCover
