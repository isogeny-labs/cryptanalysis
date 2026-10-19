import Std
import Init.Data.List.Sort.Lemmas
import Init.Grind.Ring.Basic

namespace AllAlignedOrder
open Lean.Grind

def ordered {G : Type} (l : List (Nat × G)) : List (Nat × G) :=
  l.mergeSort (fun a b => decide (a.1 ≤ b.1))

private theorem strict_of_nodup_mono {G : Type}
    (xs : List (Nat × G))
    (hmono : xs.Pairwise (fun a b => a.1 ≤ b.1))
    (hcodes : (xs.map Prod.fst).Nodup) :
    xs.Pairwise (fun a b => a.1 < b.1) := by
  induction xs with
  | nil => simp
  | cons a t ih =>
    rw [List.pairwise_cons] at hmono ⊢
    simp only [List.map_cons, List.nodup_cons] at hcodes
    constructor
    · intro b hb
      have hle := hmono.1 b hb
      have hne : a.1 ≠ b.1 := by
        intro heq
        exact hcodes.1 (heq ▸ List.mem_map.mpr ⟨b, hb, rfl⟩)
      omega
    · exact ih hmono.2 hcodes.2

/-- Equal-rotation point slots can be sorted by distinct source code while
    preserving the exact group sum. The result applies to five slots as a
    special case, without any target or characteristic assumption. -/
theorem sort_preserves_sum {G : Type} [AddCommGroup G]
    (l : List (Nat × G)) (hcodes : (l.map Prod.fst).Nodup) :
    (ordered l).Pairwise (fun a b => a.1 < b.1) ∧
    (ordered l).Perm l ∧
    (ordered l).foldl (fun sum pair => sum + pair.2) 0 =
      l.foldl (fun sum pair => sum + pair.2) 0 := by
  let le : Nat × G → Nat × G → Bool := fun a b => decide (a.1 ≤ b.1)
  have htrans : ∀ a b c : Nat × G, le a b → le b c → le a c := by
    intro a b c hab hbc
    simp only [le, decide_eq_true_eq] at hab hbc ⊢
    exact Nat.le_trans hab hbc
  have htotal : ∀ a b : Nat × G, le a b || le b a := by
    intro a b
    by_cases h : a.1 ≤ b.1
    · simp [le, h]
    · have hb : b.1 ≤ a.1 := by omega
      simp [le, hb]
  have hperm : (ordered l).Perm l := by
    exact List.mergeSort_perm l le
  have hsorted : (ordered l).Pairwise (fun a b => a.1 ≤ b.1) := by
    have h := List.pairwise_mergeSort htrans htotal l
    simpa only [ordered, le, decide_eq_true_eq] using h
  have hn : ((ordered l).map Prod.fst).Nodup := by
    exact (hperm.map Prod.fst).nodup_iff.mpr hcodes
  have hstrict := strict_of_nodup_mono (ordered l) hsorted hn
  refine ⟨hstrict, hperm, ?_⟩
  apply hperm.foldl_eq'
  intro x hx y hy z
  simp only [AddCommMonoid.add_left_comm,
             AddCommMonoid.add_comm]

/-- When all slots share one point-validity predicate, code sorting keeps
    every selected point inside that source domain. -/
theorem sort_preserves_validity {G : Type} (valid : Nat × G → Prop)
    (l : List (Nat × G))
    (hvalid : ∀ pair ∈ l, valid pair) :
    ∀ pair ∈ ordered l, valid pair := by
  intro pair hmem
  exact hvalid pair ((List.mergeSort_perm l
    (fun a b => decide (a.1 ≤ b.1))).mem_iff.mp hmem)

#print axioms sort_preserves_sum
#print axioms sort_preserves_validity

end AllAlignedOrder
