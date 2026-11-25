import Mathlib.Data.Fintype.Card
import Mathlib.Data.Finset.Card
import Mathlib.Data.Finset.Image
import Mathlib.Tactic.Linarith

namespace Prime937CuspImage

theorem image_is_identity
    {Source Target : Type*} [Fintype Source] [Nonempty Source] [DecidableEq Target]
    (map : Source → Target) (identity : Target)
    (hall_cusps : ∀ s : Source, map s = identity) :
    Finset.univ.image map = {identity} := by
  ext y
  constructor
  · intro hy
    obtain ⟨s, _, hs⟩ := Finset.mem_image.mp hy
    rw [← hs]
    exact Finset.mem_singleton.mpr (hall_cusps s)
  · intro hy
    have h : y = identity := Finset.mem_singleton.mp hy
    subst y
    obtain ⟨s⟩ := ‹Nonempty Source›
    exact Finset.mem_image.mpr ⟨s, Finset.mem_univ s, hall_cusps s⟩

theorem exactly_998_missing
    {Source Target : Type*} [Fintype Source] [Fintype Target]
    [DecidableEq Target] (map : Source → Target)
    (himage : (Finset.univ.image map).card = 1)
    (htarget : Fintype.card Target = 999) :
    ((Finset.univ : Finset Target) \ Finset.univ.image map).card = 998 := by
  have hsubset : Finset.univ.image map ⊆ (Finset.univ : Finset Target) :=
    Finset.subset_univ _
  rw [Finset.card_sdiff_of_subset hsubset]
  simp only [Finset.card_univ, htarget, himage]

#print axioms image_is_identity
#print axioms exactly_998_missing

end Prime937CuspImage
