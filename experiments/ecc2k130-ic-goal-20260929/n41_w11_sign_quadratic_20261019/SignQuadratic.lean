import Std
import Init.Grind.Ring.Basic

namespace SignQuadratic
open Lean.Grind

/-- The two-bit finite difference extracts the mixed coefficient in characteristic two. -/
theorem pair_coefficient {F : Type} [CommRing F]
    (charTwo : (1 : F) + 1 = 0) (c₀ cᵢ cⱼ cᵢⱼ : F) :
    cᵢⱼ =
      (c₀ + cᵢ + cⱼ + cᵢⱼ) +
      (c₀ + cᵢ) + (c₀ + cⱼ) + c₀ := by
  grind

def sum {G : Type} [AddCommGroup G] : List G → G
  | [] => 0
  | x :: xs => x + sum xs

def select {G : Type} [AddCommGroup G] (bit : Bool) (value : G) : G :=
  if bit then value else 0

/-- The fifteen nonconstant coefficients of a quadratic in five binary signs. -/
def terms {G : Type} [AddCommGroup G]
    (b : Fin 5 → Bool) (linear : Fin 5 → G)
    (pair : Fin 5 → Fin 5 → G) : List G :=
  [select (b 0) (linear 0), select (b 1) (linear 1),
   select (b 2) (linear 2), select (b 3) (linear 3),
   select (b 4) (linear 4),
   select (b 0 && b 1) (pair 0 1),
   select (b 0 && b 2) (pair 0 2),
   select (b 0 && b 3) (pair 0 3),
   select (b 0 && b 4) (pair 0 4),
   select (b 1 && b 2) (pair 1 2),
   select (b 1 && b 3) (pair 1 3),
   select (b 1 && b 4) (pair 1 4),
   select (b 2 && b 3) (pair 2 3),
   select (b 2 && b 4) (pair 2 4),
   select (b 3 && b 4) (pair 3 4)]

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

theorem select_annihilated {G : Type} [AddCommGroup G]
    (L : G → Bool) (hzero : L 0 = false)
    (value : G) (hv : L value = false) (bit : Bool) :
    L (select bit value) = false := by
  cases bit <;> simp [select, hzero, hv]

/-- A coordinate-linear separator excludes every assignment of all five signs. -/
theorem certificate_nonzero {G : Type} [AddCommGroup G]
    (L : G → Bool) (hzero : L 0 = false)
    (hadd : ∀ x y, L (x + y) = (L x).xor (L y))
    (base : G) (linear : Fin 5 → G) (pair : Fin 5 → Fin 5 → G)
    (hbase : L base = true)
    (hlinear : ∀ i, L (linear i) = false)
    (hpair : ∀ i j, L (pair i j) = false)
    (b : Fin 5 → Bool) :
    base + sum (terms b linear pair) ≠ 0 := by
  have hterms : ∀ x, x ∈ terms b linear pair → L x = false := by
    intro x hx
    simp only [terms, List.mem_cons, List.not_mem_nil, or_false] at hx
    rcases hx with h | h | h | h | h | h | h | h | h | h |
                  h | h | h | h | h
    all_goals
      subst x
      first
      | exact select_annihilated L hzero _ (hlinear _) _
      | exact select_annihilated L hzero _ (hpair _ _) _
  have hsum := annihilates_sum L hzero hadd (terms b linear pair) hterms
  have hvalue : L (base + sum (terms b linear pair)) = true := by
    rw [hadd, hbase, hsum]
    decide
  intro hz
  rw [hz, hzero] at hvalue
  cases hvalue

#print axioms pair_coefficient
#print axioms certificate_nonzero
end SignQuadratic
