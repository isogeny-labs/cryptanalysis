import Mathlib.Data.Fintype.Card
import Mathlib.Data.Finset.Image
import Mathlib.Tactic.Linarith

/-! Structural finite-map consequence of the exact source and target counts. -/

namespace FiniteImageGap

theorem at_least_forty_three_missing
    {Source Target : Type*} [Fintype Source] [Fintype Target] [DecidableEq Target]
    (map : Source → Target)
    (hsource : Fintype.card Source = 888)
    (htarget : Fintype.card Target = 931) :
    43 ≤ Fintype.card Target - (Finset.univ.image map).card := by
  classical
  have himage : (Finset.univ.image map).card ≤ Fintype.card Source := by
    simpa using (Finset.card_image_le (s := (Finset.univ : Finset Source)) (f := map))
  omega

#print axioms at_least_forty_three_missing

end FiniteImageGap
