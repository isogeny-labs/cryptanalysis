module

public import Mathlib.Algebra.Group.Hom.Defs
public import Mathlib.Data.Set.Basic

/-! Closed new-row combinations and induced old-only constraints. -/
namespace ClosedBridge

public def oldOnly {O N W : Type*}
    [AddCommGroup O] [AddCommGroup N] [AddCommGroup W]
    (S : Set O) (A : W →+ O) (B : W →+ N) : Set O :=
  {x | ∃ s ∈ S, ∃ w : W, x = s + A w ∧ B w = 0}

public theorem closed_image_gives_constraint {O N W : Type*}
    [AddCommGroup O] [AddCommGroup N] [AddCommGroup W]
    (S : Set O) (A : W →+ O) (B : W →+ N)
    (hzero : (0 : O) ∈ S) (w : W)
    (hclosed : B w = 0) (hnovel : A w ∉ S) :
    A w ∈ oldOnly S A B ∧ A w ∉ S := by
  constructor
  · exact ⟨0, hzero, w, by simp, hclosed⟩
  · exact hnovel

public theorem no_new_constraint_of_closed_images_mem {O N W : Type*}
    [AddCommGroup O] [AddCommGroup N] [AddCommGroup W]
    (S : Set O) (A : W →+ O) (B : W →+ N)
    (hadd : ∀ s t : O, s ∈ S → t ∈ S → s + t ∈ S)
    (hclosed : ∀ w : W, B w = 0 → A w ∈ S) :
    oldOnly S A B = S := by
  ext x
  constructor
  · rintro ⟨s, hs, w, hx, hw⟩
    rw [hx]
    exact hadd s (A w) hs (hclosed w hw)
  · intro hx
    exact ⟨x, hx, 0, by simp, by simp⟩

end ClosedBridge

#print axioms ClosedBridge.closed_image_gives_constraint
#print axioms ClosedBridge.no_new_constraint_of_closed_images_mem
