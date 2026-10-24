module

public import Mathlib.Algebra.Group.Hom.Defs
public import Mathlib.Data.Set.Basic

/-! Independent new-column projection leaves no new old-only relation. -/
namespace PrivateNewColumns

public def oldOnly {O N W : Type*}
    [AddCommGroup O] [AddCommGroup N] [AddCommGroup W]
    (S : Set O) (A : W →+ O) (B : W →+ N) : Set O :=
  {x | ∃ s ∈ S, ∃ w : W, x = s + A w ∧ B w = 0}

public theorem oldOnly_eq_original {O N W : Type*}
    [AddCommGroup O] [AddCommGroup N] [AddCommGroup W]
    (S : Set O) (A : W →+ O) (B : W →+ N)
    (hB : Function.Injective B) : oldOnly S A B = S := by
  ext x
  constructor
  · rintro ⟨s, hs, w, hx, hw⟩
    have hw0 : w = 0 := hB (by simpa using hw)
    have hxs : x = s := by simpa [hw0] using hx
    rw [hxs]
    exact hs
  · intro hx
    refine ⟨x, hx, 0, ?_, ?_⟩
    · simp
    · simp

end PrivateNewColumns

#print axioms PrivateNewColumns.oldOnly_eq_original
