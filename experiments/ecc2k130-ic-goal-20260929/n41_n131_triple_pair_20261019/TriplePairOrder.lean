import AllAlignedOrder

namespace TriplePairOrder
open Lean.Grind

/-- Sorting the equal-domain triple and equal-domain pair separately preserves
    their records and combined group sum. The records can carry the source
    masks and folded-column labels used by the collision filter. -/
theorem sort_groups {G : Type} [AddCommGroup G]
    (triple pair : List (Nat × G))
    (htriple : (triple.map Prod.fst).Nodup)
    (hpair : (pair.map Prod.fst).Nodup) :
    (AllAlignedOrder.ordered triple).Pairwise (fun a b => a.1 < b.1) ∧
    (AllAlignedOrder.ordered pair).Pairwise (fun a b => a.1 < b.1) ∧
    ((AllAlignedOrder.ordered triple) ++
      (AllAlignedOrder.ordered pair)).Perm (triple ++ pair) ∧
    (AllAlignedOrder.ordered triple).foldl (fun sum item => sum + item.2) 0 +
      (AllAlignedOrder.ordered pair).foldl (fun sum item => sum + item.2) 0 =
    triple.foldl (fun sum item => sum + item.2) 0 +
      pair.foldl (fun sum item => sum + item.2) 0 := by
  have ht := AllAlignedOrder.sort_preserves_sum triple htriple
  have hp := AllAlignedOrder.sort_preserves_sum pair hpair
  refine ⟨ht.1, hp.1, ht.2.1.append hp.2.1, ?_⟩
  rw [ht.2.2, hp.2.2]

/-- Each sorted group keeps its own source-domain predicate. The predicates
    may differ between the two Frobenius rotations. -/
theorem sort_groups_preserve_domains {G : Type}
    (valid₀ valid₁ : Nat × G → Prop)
    (triple pair : List (Nat × G))
    (htriple : ∀ item ∈ triple, valid₀ item)
    (hpair : ∀ item ∈ pair, valid₁ item) :
    (∀ item ∈ AllAlignedOrder.ordered triple, valid₀ item) ∧
    (∀ item ∈ AllAlignedOrder.ordered pair, valid₁ item) := by
  exact ⟨AllAlignedOrder.sort_preserves_validity valid₀ triple htriple,
         AllAlignedOrder.sort_preserves_validity valid₁ pair hpair⟩

#print axioms sort_groups
#print axioms sort_groups_preserve_domains

end TriplePairOrder
