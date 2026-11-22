import Mathlib.Data.Fintype.Card
import Mathlib.Data.Finset.Card
import Mathlib.Data.Finset.Image
import Mathlib.Tactic.Linarith

namespace Prime919ImageGap

theorem exactly_813_missing
    {Source Target : Type*} [Fintype Source] [Fintype Target] [DecidableEq Target]
    (map : Source → Target)
    (himage : (Finset.univ.image map).card = 55)
    (htarget : Fintype.card Target = 868) :
    ((Finset.univ : Finset Target) \ Finset.univ.image map).card = 813 := by
  have hsubset : Finset.univ.image map ⊆ (Finset.univ : Finset Target) :=
    Finset.subset_univ _
  rw [Finset.card_sdiff_of_subset hsubset]
  simp only [Finset.card_univ, htarget, himage]

theorem uniform_fiber_total : 24 * 54 = 1296 := by
  omega

#print axioms exactly_813_missing
#print axioms uniform_fiber_total

end Prime919ImageGap
