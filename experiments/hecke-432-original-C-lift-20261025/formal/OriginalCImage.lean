import Mathlib.Data.Finset.Card
import Mathlib.Data.Fintype.Card

namespace OriginalCImage

/-- An injective paired coordinate map identifies a finite source census
    with its paired image, preserving the exact source count. -/
theorem paired_image_card
    {Source Key : Type*} [Fintype Source] [DecidableEq Key]
    (paired : Source → Key) (hinj : Function.Injective paired) :
    (Finset.univ.image paired).card = Fintype.card Source := by
  simpa using Finset.card_image_of_injective (Finset.univ : Finset Source) hinj

#print axioms paired_image_card

end OriginalCImage
