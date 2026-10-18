import Std
import Init.Grind.Ring.Basic

namespace NoQuadraticFilter
open Lean.Grind

def sumList {V : Type} [CommRing V] : List V → V
  | [] => 0
  | x :: xs => x + sumList xs

/-- The evaluation feature vectors of a family generate the entire
coefficient-dual space as finite sums. For binary vectors this is
equivalent to full binary matrix rank. -/
def fullSpan {V : Type} [CommRing V] (S : V → Prop) : Prop :=
  ∀ z : V, ∃ xs : List V, (∀ x, x ∈ xs → S x) ∧ sumList xs = z

/-- A quadratic polynomial evaluates by an additive coefficient
functional on the vector of its constant, linear, and quadratic
monomials. If the feature vectors have full span and it vanishes on
each family output, its functional vanishes everywhere. -/
theorem no_nonzero_filter {V F : Type} [CommRing V] [CommRing F]
    (S : V → Prop) (evaluate : V → F)
    (hadd : ∀ x y, evaluate (x+y) = evaluate x + evaluate y)
    (hzero : evaluate 0 = 0)
    (hspan : fullSpan S)
    (hvanish : ∀ x, S x → evaluate x = 0) :
    ∀ z, evaluate z = 0 := by
  intro z
  obtain ⟨xs, hxs, hsum⟩ := hspan z
  have hlist : ∀ ys : List V,
      (∀ x, x ∈ ys → S x) → evaluate (sumList ys) = 0 := by
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
          evaluate (sumList (x :: tail)) =
              evaluate x + evaluate (sumList tail) := by
                rw [sumList, hadd]
          _ = 0 + 0 := by rw [hvanish x hx, ih ht]
          _ = 0 := by grind +ring
  rw [← hsum]
  exact hlist xs hxs

#print axioms no_nonzero_filter

end NoQuadraticFilter
