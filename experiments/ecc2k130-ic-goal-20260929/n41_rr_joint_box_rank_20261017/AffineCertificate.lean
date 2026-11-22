import Std
import Init.Grind.Ring.Basic

namespace AffineCertificate
open Lean.Grind

/-- Sum a finite list of determinant-value differences. -/
def sum {G : Type} [AddCommGroup G] : List G → G
  | [] => 0
  | x :: xs => x + sum xs

/-- A binary-linear functional vanishes on every sum of values it annihilates. -/
theorem annihilates_sum {G : Type} [AddCommGroup G]
    (L : G → Bool) (hzero : L 0 = false)
    (hadd : ∀ x y, L (x + y) = (L x).xor (L y))
    (xs : List G) (hx : ∀ x, x ∈ xs → L x = false) :
    L (sum xs) = false := by
  induction xs with
  | nil => simpa [sum] using hzero
  | cons x xs ih =>
      have hhead : L x = false := hx x (by simp)
      have htail : ∀ y, y ∈ xs → L y = false := by
        intro y hy
        exact hx y (by simp [hy])
      simp [sum, hadd, hhead, ih htail]

/-- An affine value family with a separating binary trace contains no zero. -/
theorem affine_nonzero {G : Type} [AddCommGroup G]
    (L : G → Bool) (hzero : L 0 = false)
    (hadd : ∀ x y, L (x + y) = (L x).xor (L y))
    (base : G) (xs : List G)
    (hbase : L base = true)
    (hx : ∀ x, x ∈ xs → L x = false) :
    base + sum xs ≠ 0 := by
  have hsum := annihilates_sum L hzero hadd xs hx
  have hvalue : L (base + sum xs) = true := by
    rw [hadd, hbase, hsum]
    decide
  intro hz
  rw [hz, hzero] at hvalue
  cases hvalue

/-- If listed differences span every value, no nonzero binary trace
    functional annihilates all of them. -/
theorem full_span_obstruction {G : Type} [AddCommGroup G]
    (L : G → Bool) (hzero : L 0 = false)
    (hadd : ∀ x y, L (x + y) = (L x).xor (L y))
    (basis : List G)
    (hann : ∀ x, x ∈ basis → L x = false)
    (hspan : ∀ x : G, ∃ xs : List G,
      (∀ y, y ∈ xs → y ∈ basis) ∧ sum xs = x) :
    ∀ x : G, L x = false := by
  intro x
  obtain ⟨xs, hsubset, hsum⟩ := hspan x
  have hx : ∀ y, y ∈ xs → L y = false := by
    intro y hy
    exact hann y (hsubset y hy)
  rw [← hsum]
  exact annihilates_sum L hzero hadd xs hx

#print axioms affine_nonzero
#print axioms full_span_obstruction
end AffineCertificate
