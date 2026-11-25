import Mathlib.Data.Finset.Card
import Mathlib.Tactic.NormNum

namespace ExactBImage

variable {β : Type*} [DecidableEq β]

/-- A disjoint partition into 72 complete fibers and six partial fibers,
plus the cusp identity, has 79 image points. -/
theorem image_card_from_fiber_partition
    (complete half : Finset β) (identity : β)
    (hcomplete : complete.card = 72) (hhalf : half.card = 6)
    (hdisjoint : Disjoint complete half)
    (hidentity : identity ∉ complete ∪ half) :
    (insert identity (complete ∪ half)).card = 79 := by
  rw [Finset.card_insert_of_notMem hidentity,
      Finset.card_union_of_disjoint hdisjoint, hcomplete, hhalf]

/-- Given a 1008-point group, exactly 929 points lie outside this image. -/
theorem complement_card_from_exact_image [Fintype β]
    (image : Finset β) (hgroup : (Finset.univ : Finset β).card = 1008)
    (himage : image.card = 79) :
    (Finset.univ \ image).card = 929 := by
  rw [Finset.card_sdiff_of_subset (Finset.subset_univ image)]
  norm_num [hgroup, himage]

#print axioms image_card_from_fiber_partition
#print axioms complement_card_from_exact_image

end ExactBImage
