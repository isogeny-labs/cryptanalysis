import Std
import Init.Grind.Ring.Basic

namespace TopDegreeSpan
open Lean.Grind

def sumList {F : Type} [CommRing F] : List F → F
  | [] => 0
  | x :: xs => x + sumList xs

/-- Every vector is a finite sum of members of `S`. In a binary vector
space, this is exactly the full-rank span condition. -/
def fullSpan {F : Type} [CommRing F] (S : F → Prop) : Prop :=
  ∀ z : F, ∃ xs : List F, (∀ x, x ∈ xs → S x) ∧ sumList xs = z

/-- A map that is additive and vanishes on a full-span family vanishes
on every vector. -/
theorem full_span_annihilator_zero {F G : Type}
    [CommRing F] [CommRing G]
    (S : F → Prop) (φ : F → G)
    (hadd : ∀ x y, φ (x + y) = φ x + φ y)
    (hzero : φ 0 = 0)
    (hspan : fullSpan S)
    (hvanish : ∀ x, S x → φ x = 0) :
    ∀ z, φ z = 0 := by
  intro z
  obtain ⟨xs, hxs, hsum⟩ := hspan z
  have hlist : ∀ ys : List F,
      (∀ x, x ∈ ys → S x) → φ (sumList ys) = 0 := by
    intro ys
    induction ys with
    | nil =>
        intro _
        simpa [sumList] using hzero
    | cons x tail ih =>
        intro hall
        have hx : S x := hall x (by simp)
        have ht : ∀ y, y ∈ tail → S y := by
          intro y hy
          exact hall y (by simp [hy])
        calc
          φ (sumList (x :: tail)) = φ x + φ (sumList tail) := by
            rw [sumList, hadd]
          _ = 0 + 0 := by rw [hvanish x hx, ih ht]
          _ = 0 := by grind +ring
  rw [← hsum]
  exact hlist xs hxs

#print axioms full_span_annihilator_zero

end TopDegreeSpan
