import Mathlib.Tactic
import Mathlib.Data.ZMod.Basic

namespace M31.WordMarginal

abbrev Word := Fin 18446744073709551616
abbrev G := ZMod 2147505293
abbrev maxPreimages := 8589848013

def address (w : Word) (d : G) : G := (w.val : G) + d

/-- Index each preimage by its translated residue and its integer quotient. -/
theorem single (hits : Finset G) (d : G) :
    (Finset.univ.filter (fun w : Word => address w d ∈ hits)).card ≤ hits.card * maxPreimages := by
  classical
  let S := Finset.univ.filter (fun w : Word => address w d ∈ hits)
  let encode (x : S) : hits × Fin maxPreimages :=
    (⟨address x.val d, (Finset.mem_filter.mp x.property).2⟩,
     ⟨x.val.val / 2147505293, by have h := x.val.isLt; unfold maxPreimages; omega⟩)
  have inj : Function.Injective encode := by
    intro x y e
    have hr : address x.val d = address y.val d := congrArg (fun z => z.1.val) e
    have hd : x.val.val / 2147505293 = y.val.val / 2147505293 := congrArg (fun z => z.2.val) e
    have hm := congrArg ZMod.val (add_right_cancel hr : (x.val.val : G) = (y.val.val : G))
    simp only [ZMod.val_natCast] at hm
    apply Subtype.ext
    apply Fin.ext
    omega
  simpa only [Fintype.card_prod, Fintype.card_coe, Fintype.card_fin] using Fintype.card_le_of_injective encode inj

private theorem filter_weight {α : Type*} (domain : Finset α) (pred : α → Prop)
    [DecidablePred pred] :
    (domain.filter pred).card * 3 = ∑ a ∈ domain, if pred a then 3 else (0 : ℕ) := by
  rw [← Finset.sum_filter, Finset.sum_const, nsmul_eq_mul, Nat.cast_id]

/-- Each slot may permute the common uniform word separately, allowing arbitrary
dependence arising from these permutations. The displacement is fixed per slot. -/
theorem deadline {Q : Type*} (slots : Finset Q) (perm : Q → Word ≃ Word)
    (delta : Q → G) (hits : Finset G) (size : hits.card = 578)
    (budget : slots.card ≤ 82000) :
    1000000 * (Finset.univ.filter (fun w : Word => 3 ≤ ∑ j ∈ slots,
      if address (perm j w) (delta j) ∈ hits then 1 else (0 : ℕ))).card <
      7357 * 18446744073709551616 := by
  classical
  let hit (w : Word) (j : Q) : ℕ := if address (perm j w) (delta j) ∈ hits then 1 else 0
  let S := Finset.univ.filter (fun w : Word => 3 ≤ ∑ j ∈ slots, hit w j)
  have hs (j : Q) : (∑ w : Word, hit w j) ≤ 578 * maxPreimages := by
    calc
      _ = ∑ w : Word, if address w (delta j) ∈ hits then 1 else 0 :=
        Equiv.sum_comp (perm j) _
      _ ≤ _ := by
        rw [Finset.sum_boole, Nat.cast_id]
        simpa only [size] using single hits (delta j)
  have h : S.card * 3 ≤ slots.card * (578 * maxPreimages) := by
    calc
      _ = ∑ w : Word, if 3 ≤ ∑ j ∈ slots, hit w j then 3 else 0 := by
        exact filter_weight Finset.univ _
      _ ≤ ∑ w : Word, ∑ j ∈ slots, hit w j := by
        apply Finset.sum_le_sum
        intro w _
        split <;> omega
      _ = ∑ j ∈ slots, ∑ w : Word, hit w j := Finset.sum_comm
      _ ≤ ∑ _j ∈ slots, 578 * maxPreimages := Finset.sum_le_sum fun j _ => hs j
      _ = _ := by simp
  change 1000000 * S.card < _
  unfold maxPreimages at h
  omega

end M31.WordMarginal
