import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Int.Interval
import Mathlib.Tactic

namespace XedniNonisomorphicFamily


private def image (q : ℕ) (u : ZMod q) : Finset (ZMod q) :=
  (Finset.Icc (-4 : ℤ) 4).image (fun k : ℤ => (k : ZMod q) * u)

private def pairUnion (q : ℕ) [NeZero q] : Finset (ZMod q × ZMod q) :=
  (image q 1).product (image q 1) ∪
    (image q 3).product (image q 3)

private theorem pair_card_of_sizes {α : Type*} [DecidableEq α]
    (S T : Finset α) (hS : S.card = 9) (hT : T.card = 9)
    (hI : (S ∩ T).card = 3) :
    ((S.product S) ∪ (T.product T)).card = 153 := by
  have hinter : (S.product S) ∩ (T.product T) =
      (S ∩ T).product (S ∩ T) := by
    ext pair
    simp [and_left_comm, and_assoc]
  have hSI : (S.product S).card = 81 := by
    simp [Finset.card_product, hS]
  have hTI : (T.product T).card = 81 := by
    simp [Finset.card_product, hT]
  have hII : ((S.product S) ∩ (T.product T)).card = 9 := by
    rw [hinter]
    simp [Finset.card_product, hI]
  have hsum := Finset.card_union_add_card_inter (S.product S) (T.product T)
  rw [hSI, hTI, hII] at hsum
  omega

/-- Exact support of the two checked generator images at subgroup order 599. -/
theorem pair_union_card_599 : (pairUnion 599).card = 153 := by
  apply pair_card_of_sizes
  · decide
  · decide
  · decide

/-- Exact support of the two checked generator images at subgroup order 353. -/
theorem pair_union_card_353 : (pairUnion 353).card = 153 := by
  apply pair_card_of_sizes
  · decide
  · decide
  · decide

#print axioms pair_union_card_599
#print axioms pair_union_card_353

end XedniNonisomorphicFamily
