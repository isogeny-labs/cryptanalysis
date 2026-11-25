import Mathlib.Tactic
import Mathlib.Combinatorics.Enumerative.InclusionExclusion
import Mathlib.Data.Nat.Choose.Sum

namespace M31.DeadlineOccupancy

/-- A specified r-label subset admits m miss symbols plus two symbols for each
label. All histories counted here therefore automatically avoid outside labels. -/
abbrev Symbol (m r : ℕ) := Fin m ⊕ (Fin r × Fin 2)

def label {m r : ℕ} : Symbol m r → Option (Fin r)
  | .inl _ => none
  | .inr (i, _) => some i

private theorem inf_mem {I X : Type*} [Fintype X] [DecidableEq X]
    (s : Finset I) (sets : I → Finset X) (x : X) :
    x ∈ s.inf sets ↔ ∀ i ∈ s, x ∈ sets i := by
  classical
  induction s using Finset.induction_on with
  | empty => simp
  | insert a s ha ih => simp [ih]

def complete (m r n : ℕ) := Finset.univ.filter
  (fun h : Fin n → Symbol m r => ∀ i : Fin r, ∃ j, label (h j) = some i)

theorem exact_set (m r n : ℕ) :
    ((complete m r n).card : ℤ) =
      ∑ t ∈ (Finset.univ : Finset (Fin r)).powerset,
        (-1 : ℤ)^t.card * ((m + (r-t.card)*2 : ℕ) : ℤ)^n := by
  classical
  let missing (i : Fin r) := Finset.univ.filter
    (fun h : Fin n → Symbol m r => ∀ j, label (h j) ≠ some i)
  have allSeen : complete m r n = Finset.univ.inf (fun i => (missing i)ᶜ) := by
    ext h
    simp [complete, inf_mem, missing]
  rw [allSeen, Finset.inclusion_exclusion_card_inf_compl]
  apply Finset.sum_congr rfl
  intro t _
  let alphabet : Finset (Symbol m r) :=
    Finset.univ.disjSum ((tᶜ).product (Finset.univ : Finset (Fin 2)))
  have without : t.inf missing = Fintype.piFinset (fun _ : Fin n => alphabet) := by
    ext h
    simp only [inf_mem, missing, Finset.mem_filter, Finset.mem_univ, true_and,
      Fintype.mem_piFinset]
    have single (x : Symbol m r) : x ∈ alphabet ↔ ∀ i ∈ t, label x ≠ some i := by
      cases x with
      | inl x => simp [alphabet, label]
      | inr x => simp [alphabet, label]
    simp_rw [single]
    exact ⟨fun a j i hi => a i hi j, fun a i hi j => a j i hi⟩
  rw [without, Fintype.card_piFinset_const]
  simp [alphabet, Finset.card_compl]

/-- Group the subsets by the number of forbidden labels. This is the
binomial form evaluated in the fixed-deadline reference calculation. -/
theorem binomial_count (m r n : ℕ) :
    ((complete m r n).card : ℤ) =
      ∑ k ∈ Finset.range (r+1), (r.choose k : ℤ) *
        ((-1 : ℤ)^k * ((m + (r-k)*2 : ℕ) : ℤ)^n) := by
  rw [exact_set]
  simpa only [Finset.card_univ, Fintype.card_fin, nsmul_eq_mul] using
    (Finset.sum_powerset_apply_card (x := (Finset.univ : Finset (Fin r)))
      (fun k => (-1 : ℤ)^k * ((m + (r-k)*2 : ℕ) : ℤ)^n))

end M31.DeadlineOccupancy
