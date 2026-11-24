import MixedCover

namespace M31PeriodicCover
open M31TerminalSeparation M31ArchiveData

def paths (x depth : Nat) := ((List.range (depth+1)).map (fun n => label n x)).toFinset

-- Twelve archived inputs with pairwise disjoint paths through depth 28.
private def witnesses : Finset Nat := [3, 98625645, 308768278, 536276641, 975624154, 985108144, 1171458932, 1213058799, 1685732321, 1896314920, 1900239952, 2084456163].toFinset

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
private theorem checked_witnesses :
    witnesses.card = 12 ∧ (∀ x ∈ witnesses, x ∈ archived.map Prod.fst) ∧
    ∀ x ∈ witnesses, ∀ y ∈ witnesses, x = y ∨ Disjoint (paths x 28) (paths y 28) := by
  decide +kernel

theorem bounded_lower (targets : Finset Nat)
    (cover : ∀ q ∈ archived, ∃ n ≤ 28, label n q.1 ∈ targets) : 12 ≤ targets.card := by
  classical
  obtain ⟨size, member, apart⟩ := checked_witnesses
  have existsTarget (x : Nat) (hx : x ∈ witnesses) : ∃ t ∈ targets, t ∈ paths x 28 := by
    obtain ⟨q,hq,rfl⟩ := List.mem_map.mp (member x hx)
    obtain ⟨n,hn,ht⟩ := cover q hq
    exact ⟨_,ht,List.mem_toFinset.mpr (List.mem_map.mpr ⟨n,List.mem_range.mpr (by omega),rfl⟩)⟩
  let pick (x : Nat) := if h : x ∈ witnesses then (existsTarget x h).choose else 0
  have chosen (x : Nat) (hx : x ∈ witnesses) : pick x ∈ targets ∧ pick x ∈ paths x 28 := by
    simpa only [pick,hx,↓reduceDIte] using (existsTarget x hx).choose_spec
  have inj : Set.InjOn pick witnesses := by
    intro x hx y hy eq
    rcases apart x hx y hy with same | disjoint
    · exact same
    · exact False.elim ((Finset.disjoint_left.mp disjoint) (chosen x hx).2 (eq ▸ (chosen y hy).2))
  have sub : witnesses.image pick ⊆ targets := by
    intro t ht
    obtain ⟨x,hx,rfl⟩ := Finset.mem_image.mp ht
    exact (chosen x hx).1
  rw [← size, ← Finset.card_image_of_injOn inj]
  exact Finset.card_le_card sub

-- Keep the original abscissa for singleton classes and use zero for the shared class.
private def shortTargets := (archived.map (fun q => if label 31 q.1 = 2 then 0 else q.1)).toFinset

set_option maxRecDepth 32768 in
theorem bounded_upper : shortTargets.card = 11 ∧
    ∀ q ∈ archived, ∃ n : Fin 30, label n.val q.1 ∈ shortTargets := by decide +kernel

theorem first_mixed_horizon (depth : Nat) :
    (∃ ts : Finset Nat, ts.card = 11 ∧ ∀ q ∈ archived, ∃ n ≤ depth, label n q.1 ∈ ts) ↔
      29 ≤ depth := by
  constructor
  · rintro ⟨ts,hsize,hcover⟩
    by_contra h
    have impossible := bounded_lower ts (fun q hq => by
      obtain ⟨n,hn,ht⟩ := hcover q hq
      exact ⟨n,by omega,ht⟩)
    omega
  · intro hd
    refine ⟨shortTargets,bounded_upper.1,?_⟩
    intro q hq
    obtain ⟨n,hn⟩ := bounded_upper.2 q hq
    exact ⟨n.val,by have := n.isLt; omega,hn⟩

end M31PeriodicCover
