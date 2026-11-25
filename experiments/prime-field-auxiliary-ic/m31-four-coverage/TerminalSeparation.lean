import Mathlib.Tactic
import ArchiveData
import ArchiveRoots

namespace M31TerminalSeparation
open M31ArchiveData M31ArchiveRoots

-- Canonical residues of x²-2 modulo 2³¹-1, with subtraction in Nat.
def step (x : Nat) : Nat := (x*x+2147483645)%2147483647
def label (d x : Nat) := step^[d] x

theorem archived_in_roots : ∀ q ∈ archived, q.1 ∈ roots := by decide +kernel

set_option maxRecDepth 32768 in
private theorem separated24 :
    roots.all (fun x => roots.all (fun y => decide (label 24 x ≠ label 24 y ∨ x = y))) := by
  decide +kernel

theorem unique_terminal {x y d : Nat} (hx : x ∈ roots) (hy : y ∈ roots)
    (hd : d ≤ 24) (same : label d x = label d y) : x = y := by
  have hd24 : label 24 x = label 24 y := by
    have h := congrArg (step^[24-d]) same
    unfold label at *
    simpa only [← Function.iterate_add_apply, Nat.sub_add_cancel hd] using h
  have pair := List.all_eq_true.mp (List.all_eq_true.mp separated24 x hx) y hy
  exact (of_decide_eq_true pair).resolve_left (fun h => h hd24)

theorem archived_seven {a b : Nat × Nat} (ha : a ∈ archived) (hb : b ∈ archived)
    (same : label 7 a.1 = label 7 b.1) : a.1 = b.1 :=
  unique_terminal (archived_in_roots a ha) (archived_in_roots b hb) (by decide) same

set_option maxRecDepth 32768 in
theorem first_collision :
    ((roots.map (label 25)).eraseDups.length = 30) ∧
    ((archived.map (fun q => label 25 q.1)).eraseDups.length = 16) := by decide +kernel

theorem published_terminal :
    public71.all (fun q => decide (label 7 q.1 = 340921998)) := by decide +kernel

def archivedLabels : Finset Nat := (archived.map (fun q => label 7 q.1)).toFinset

theorem minimum_cover (terminals : Finset Nat)
    (covers : ∀ q ∈ archived, label 7 q.1 ∈ terminals) : 17 ≤ terminals.card := by
  have sub : archivedLabels ⊆ terminals := by
    intro t ht
    obtain ⟨q, hq, rfl⟩ := List.mem_map.mp (List.mem_toFinset.mp ht)
    exact covers q hq
  have size : archivedLabels.card = 17 := by decide +kernel
  rw [← size]
  exact Finset.card_le_card sub

theorem attainable :
    archivedLabels.card = 17 ∧ ∀ q ∈ archived, label 7 q.1 ∈ archivedLabels := by
  constructor
  · decide +kernel
  · intro q hq
    exact List.mem_toFinset.mpr (List.mem_map.mpr ⟨q,hq,rfl⟩)

end M31TerminalSeparation
