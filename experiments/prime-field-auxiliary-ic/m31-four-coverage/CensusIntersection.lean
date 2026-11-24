import CensusCard

namespace M31CensusCard
open Finset

def onCurve (s : Finset (F × F)) :=
  ∀ a ∈ s, a.2^2 = a.1^3 + 2*a.1 + 14

def signClosed (s : Finset (F × F)) :=
  ∀ a ∈ s, (a.1,-a.2) ∈ s

theorem project_intersection (s t : Finset (F × F))
    (cs : onCurve s) (ct : onCurve t) (nt : signClosed t) :
    (s ∩ t).image Prod.fst = s.image Prod.fst ∩ t.image Prod.fst := by
  ext x
  constructor
  · intro h
    obtain ⟨a, ha, rfl⟩ := mem_image.mp h
    exact mem_inter.mpr ⟨mem_image_of_mem _ (mem_inter.mp ha).1,
      mem_image_of_mem _ (mem_inter.mp ha).2⟩
  · intro h
    obtain ⟨hs, ht⟩ := mem_inter.mp h
    obtain ⟨⟨u,y⟩, hy, rfl⟩ := mem_image.mp hs
    obtain ⟨⟨v,z⟩, hz, hv⟩ := mem_image.mp ht
    change v = u at hv
    subst v
    have squares : y^2 = z^2 := (cs _ hy).trans (ct _ hz).symm
    have mem : (u,y) ∈ t := by
      rcases sq_eq_sq_iff_eq_or_eq_neg.mp squares with eq | eq
      · simpa [eq] using hz
      · rw [eq]
        exact nt _ hz
    exact mem_image.mpr ⟨(u,y), mem_inter.mpr ⟨hy,mem⟩,rfl⟩

theorem intersection_card (s t : Finset (F × F))
    (cs : onCurve s) (ct : onCurve t) (ns : signClosed s) (nt : signClosed t) :
    (s ∩ t).card = 2 * (s.image Prod.fst ∩ t.image Prod.fst).card := by
  rw [← project_intersection s t cs ct nt]
  apply card_points
  · intro a ha
    exact cs _ (mem_inter.mp ha).1
  · intro a ha
    exact mem_inter.mpr ⟨ns _ (mem_inter.mp ha).1, nt _ (mem_inter.mp ha).2⟩

#print axioms intersection_card
end M31CensusCard
