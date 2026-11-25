import Mathlib

namespace M31SupportRank
open Finset

set_option maxRecDepth 16384 in
/-- Conditional on the census size and coverage by unordered signed triples. -/
theorem labels_needed {X : Type*} [DecidableEq X] (n : ℕ)
    (eval : Sym (Fin (2*n)) 3 → X) (points : Finset X)
    (hsize : points.card = 3439976) (covers : points ⊆ univ.image eval) : 137 ≤ n := by
  classical
  have h := (card_le_card covers).trans card_image_le
  rw [hsize, card_univ, Sym.card_sym_eq_multichoose, Fintype.card_fin, Nat.multichoose_eq] at h
  by_contra! small
  have bound : 2*n + 3 - 1 ≤ 274 := by omega
  have h' := Nat.choose_le_choose 3 bound
  have cap : Nat.choose 274 3 = 3391024 := by decide +kernel
  omega

theorem zero_on_span {K I : Type*} [Field K] (rows : Set (I → K)) (i : I)
    (zeroAt : ∀ v ∈ rows, v i = 0) (v : I → K) (hv : v ∈ Submodule.span K rows) :
    v i = 0 := by
  induction hv using Submodule.span_induction with
  | mem x hx => exact zeroAt x hx
  | zero => rfl
  | add x y _ _ hx hy => simp [Pi.add_apply, hx, hy]
  | smul a x _ hx => simp [Pi.smul_apply, hx]

/-- Every extension by original seven-term rows needs at least nine rows
when their span contains vectors nonzero on at least 137 labels and the
old generators use at most 74. The spanning family need not be independent. -/
theorem extension_size {K I R : Type*} [Field K] [DecidableEq I]
    (old : Set (I → K)) (oldLabels used : Finset I)
    (ids : Finset R) (row : R → I → K) (supp : R → Finset I)
    (hold : oldLabels.card ≤ 74) (hused : 137 ≤ used.card)
    (oldZero : ∀ v ∈ old, ∀ i ∉ oldLabels, v i = 0)
    (newZero : ∀ r ∈ ids, ∀ i ∉ supp r, row r i = 0)
    (sparse : ∀ r ∈ ids, (supp r).card ≤ 7)
    (active : ∀ i ∈ used, ∃ v ∈ Submodule.span K (old ∪ row '' (ids : Set R)), v i ≠ 0) :
    9 ≤ ids.card := by
  classical
  have cover : used ⊆ oldLabels ∪ ids.biUnion supp := by
    intro i hi
    by_contra missing
    obtain ⟨v, hv, hn⟩ := active i hi
    apply hn
    apply zero_on_span _ i _ v hv
    intro w hw
    rcases hw with hw | ⟨r, hr, rfl⟩
    · exact oldZero w hw i (fun x => missing (mem_union_left _ x))
    · exact newZero r hr i (fun x => missing (mem_union_right _ (mem_biUnion.mpr ⟨r, hr, x⟩)))
  have h₁ := (card_le_card cover).trans (card_union_le _ _)
  have h₂ : (ids.biUnion supp).card ≤ ids.card * 7 := by
    calc
      _ ≤ ∑ r ∈ ids, (supp r).card := card_biUnion_le
      _ ≤ ∑ _r ∈ ids, 7 := sum_le_sum sparse
      _ = _ := by simp
  omega

end M31SupportRank
