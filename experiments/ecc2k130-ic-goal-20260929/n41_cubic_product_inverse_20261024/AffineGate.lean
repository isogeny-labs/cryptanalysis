import Std

open Lean.Grind

/-!
Soundness of the characteristic-two affine screen used for each four-root
half of the N41 third-product inverse.  The actual generator list contains
the root's constant shift and the image of every source-product basis element.
-/

namespace AffineGate

def xorSum {K : Type} [CommRing K] : List K → K
  | [] => 0
  | x :: xs => x + xorSum xs

def image {K : Type} [CommRing K] (c1 c2 x : K) : K :=
  c1 * x + c2 * x^2

def inSpan {K : Type} [CommRing K] (columns : List K) (value : K) : Prop :=
  ∃ selected : List K,
    (∀ x, x ∈ selected → x ∈ columns) ∧ xorSum selected = value

theorem image_add {K : Type} [CommRing K] (h2 : (2 : K) = 0)
    (c1 c2 x y : K) : image c1 c2 (x + y) = image c1 c2 x + image c1 c2 y := by
  unfold image
  grind +ring

theorem image_sum {K : Type} [CommRing K] (h2 : (2 : K) = 0)
    (c1 c2 : K) (xs : List K) :
    image c1 c2 (xorSum xs) = xorSum (xs.map (image c1 c2)) := by
  induction xs with
  | nil => simp [xorSum, image]; grind +ring
  | cons x xs ih =>
      simp only [xorSum, List.map_cons]
      rw [image_add h2, ih]

/-- Any true product witness forces the half's anchor into the span generated
    by the root shift and the images of the source-product basis. -/
theorem true_witness_passes_half {K : Type} [CommRing K] (h2 : (2 : K) = 0)
    (anchor c0 c1 c2 : K) (basis columns selected : List K)
    (hselected : ∀ x, x ∈ selected → x ∈ basis)
    (hshift : anchor + c0 ∈ columns)
    (himages : ∀ x, x ∈ basis → image c1 c2 x ∈ columns)
    (hroot : c0 + image c1 c2 (xorSum selected) = 0) :
    inSpan columns anchor := by
  refine ⟨(anchor + c0) :: selected.map (image c1 c2), ?_, ?_⟩
  · intro x hx
    simp only [List.mem_cons, List.mem_map] at hx
    rcases hx with heq | ⟨y, hy, heq⟩
    · simpa [heq] using hshift
    · subst x
      exact himages y (hselected y hy)
  · simp only [xorSum]
    rw [← image_sum h2]
    grind

#print axioms AffineGate.image_add
#print axioms AffineGate.image_sum
#print axioms AffineGate.true_witness_passes_half

end AffineGate
