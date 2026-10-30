module

public import Mathlib.Data.Finset.Basic

/-!
Appending source k adds exactly the relations whose greatest source index is k
to the relation set already available at count k. The executable collector's
claim that it emits that exact delta is checked against the static enumerator.
-/

namespace IncrementalPrefix

variable {R : Type*} [DecidableEq R]

public def available (rows : Finset R) (maxSource : R → Nat) (count : Nat) : Finset R :=
  rows.filter (fun row => maxSource row < count)

public theorem prefix_step (rows : Finset R) (maxSource : R → Nat) (k : Nat) :
    available rows maxSource (k + 1) =
      available rows maxSource k ∪ rows.filter (fun row => maxSource row = k) := by
  classical
  ext row
  simp only [available, Finset.mem_filter, Finset.mem_union]
  constructor
  · rintro ⟨hmem, hlt⟩
    rcases lt_or_eq_of_le (Nat.lt_succ_iff.mp hlt) with hlt' | heq
    · exact Or.inl ⟨hmem, hlt'⟩
    · exact Or.inr ⟨hmem, heq⟩
  · rintro (⟨hmem, hlt⟩ | ⟨hmem, heq⟩)
    · exact ⟨hmem, lt_trans hlt (Nat.lt_succ_self k)⟩
    · exact ⟨hmem, heq ▸ Nat.lt_succ_self k⟩

public theorem prefix_mono (rows : Finset R) (maxSource : R → Nat)
    {k l : Nat} (hkl : k ≤ l) :
    available rows maxSource k ⊆ available rows maxSource l := by
  classical
  intro row hr
  simp only [available, Finset.mem_filter] at hr ⊢
  exact ⟨hr.1, lt_of_lt_of_le hr.2 hkl⟩

#print axioms prefix_step
#print axioms prefix_mono

end IncrementalPrefix
