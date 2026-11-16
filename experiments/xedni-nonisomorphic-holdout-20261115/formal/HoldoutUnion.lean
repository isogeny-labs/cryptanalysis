import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Int.Interval
import Mathlib.Tactic

namespace XedniNonisomorphicHoldout

private def image (q : ℕ) (u : ZMod q) : Finset (ZMod q) :=
  (Finset.Icc (-4 : ℤ) 4).image (fun k : ℤ => (k : ZMod q) * u)

private def pairUnion (q : ℕ) [NeZero q] (u : ZMod q) : Finset (ZMod q × ZMod q) :=
  (image q 1).product (image q 1) ∪ (image q u).product (image q u)

private theorem pair_card_five {α : Type*} [DecidableEq α]
    (S T : Finset α) (hS : S.card = 9) (hT : T.card = 9)
    (hI : (S ∩ T).card = 5) :
    ((S.product S) ∪ (T.product T)).card = 137 := by
  have hinter : (S.product S) ∩ (T.product T) =
      (S ∩ T).product (S ∩ T) := by
    ext pair
    simp [and_left_comm, and_assoc]
  have hSI : (S.product S).card = 81 := by simp [Finset.card_product, hS]
  have hTI : (T.product T).card = 81 := by simp [Finset.card_product, hT]
  have hII : ((S.product S) ∩ (T.product T)).card = 25 := by
    rw [hinter]
    simp [Finset.card_product, hI]
  have hsum := Finset.card_union_add_card_inter (S.product S) (T.product T)
  rw [hSI, hTI, hII] at hsum
  omega

private theorem pair_card_three {α : Type*} [DecidableEq α]
    (S T : Finset α) (hS : S.card = 9) (hT : T.card = 9)
    (hI : (S ∩ T).card = 3) :
    ((S.product S) ∪ (T.product T)).card = 153 := by
  have hinter : (S.product S) ∩ (T.product T) =
      (S ∩ T).product (S ∩ T) := by
    ext pair
    simp [and_left_comm, and_assoc]
  have hSI : (S.product S).card = 81 := by simp [Finset.card_product, hS]
  have hTI : (T.product T).card = 81 := by simp [Finset.card_product, hT]
  have hII : ((S.product S) ∩ (T.product T)).card = 9 := by
    rw [hinter]
    simp [Finset.card_product, hI]
  have hsum := Finset.card_union_add_card_inter (S.product S) (T.product T)
  rw [hSI, hTI, hII] at hsum
  omega

/-- Radius-four pair support for the 773 field and the qualified u=2 model. -/
theorem pair_union_card_751 : (pairUnion 751 2).card = 137 := by
  apply pair_card_five
  · decide
  · decide
  · decide

/-- Radius-four pair support for the 883 field and the qualified u=2 model. -/
theorem pair_union_card_883 : (pairUnion 883 2).card = 137 := by
  apply pair_card_five
  · decide
  · decide
  · decide

/-- Radius-four pair support for the 983 field and the qualified u=3 model. -/
theorem pair_union_card_983 : (pairUnion 983 3).card = 153 := by
  apply pair_card_three
  · decide
  · decide
  · decide

#print axioms pair_union_card_751
#print axioms pair_union_card_883
#print axioms pair_union_card_983

end XedniNonisomorphicHoldout
