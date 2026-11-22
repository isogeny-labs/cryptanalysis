import Std
import Init.Grind.Ring.Basic

open Lean.Grind

namespace TraceCertificate

/-- Sum the nonconstant ANF coefficients selected by one Boolean assignment. -/
def tailSum {R : Type} [CommRing R] : List R → R
  | [] => 0
  | x :: xs => x + tailSum xs

/-- A binary linear functional annihilates any sum of coefficients that it
annihilates individually. -/
theorem tailSum_zero {R : Type} [CommRing R]
    (ell : R → Bool)
    (ell_zero : ell 0 = false)
    (ell_add : ∀ x y, ell (x + y) = Bool.xor (ell x) (ell y))
    (xs : List R)
    (annihilates : ∀ x ∈ xs, ell x = false) :
    ell (tailSum xs) = false := by
  induction xs with
  | nil => simpa [tailSum] using ell_zero
  | cons x rest ih =>
      have hx : ell x = false := annihilates x (by simp)
      have hr : ∀ y ∈ rest, ell y = false := by
        intro y hy
        exact annihilates y (by simp [hy])
      simp only [tailSum, ell_add, hx, ih hr]
      decide

/-- When the constant coefficient has functional value one and every
nonconstant ANF coefficient has value zero, every assignment has nonzero
polynomial value. -/
theorem certificate_excludes_zero {R : Type} [CommRing R]
    (ell : R → Bool)
    (ell_zero : ell 0 = false)
    (ell_add : ∀ x y, ell (x + y) = Bool.xor (ell x) (ell y))
    (constant : R) (selected : List R)
    (constant_one : ell constant = true)
    (annihilates : ∀ x ∈ selected, ell x = false) :
    constant + tailSum selected ≠ 0 := by
  have h : ell (constant + tailSum selected) = true := by
    rw [ell_add, constant_one, tailSum_zero ell ell_zero ell_add selected annihilates]
    decide
  intro hz
  rw [hz, ell_zero] at h
  contradiction

#print axioms tailSum_zero
#print axioms certificate_excludes_zero

end TraceCertificate
