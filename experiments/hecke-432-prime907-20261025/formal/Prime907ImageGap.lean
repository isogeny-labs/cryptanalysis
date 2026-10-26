import Mathlib.Data.Fintype.Card
import Mathlib.Data.Finset.Card
import Mathlib.Data.Finset.Image
import Mathlib.Tactic.Linarith

namespace Prime907ImageGap

theorem exactly_858_missing
    {Source Target : Type*} [Fintype Source] [Fintype Target] [DecidableEq Target]
    (map : Source → Target)
    (himage : (Finset.univ.image map).card = 31)
    (htarget : Fintype.card Target = 889) :
    ((Finset.univ : Finset Target) \ Finset.univ.image map).card = 858 := by
  have hsubset : Finset.univ.image map ⊆ (Finset.univ : Finset Target) :=
    Finset.subset_univ _
  rw [Finset.card_sdiff_of_subset hsubset]
  simp only [Finset.card_univ, htarget, himage]

theorem uniform_fiber_total : 24 * 30 = 720 := by
  omega

#print axioms exactly_858_missing
#print axioms uniform_fiber_total

end Prime907ImageGap
