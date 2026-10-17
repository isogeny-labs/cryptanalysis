import Std
import Init.Grind.Ring.Basic

open Lean.Grind

namespace SparseLinearized

/-- Evaluate `c₀ x + c₁ x² + c₂ x⁴ + ...` by repeated squaring. -/
def eval {R : Type} [CommRing R] : List R → R → R
  | [], _ => 0
  | c :: cs, x => c * x + eval cs (x * x)

/-- A ring map commutes with the sparse repeated-squaring evaluation.
This is the algebraic core of reducing a linearized annihilator modulo a
small polynomial before computing its GCD. -/
theorem eval_map {R S : Type} [CommRing R] [CommRing S]
    (map : R → S)
    (map_zero : map 0 = 0)
    (map_add : ∀ a b, map (a + b) = map a + map b)
    (map_mul : ∀ a b, map (a * b) = map a * map b)
    (coeff : List R) (x : R) :
    map (eval coeff x) = eval (coeff.map map) (map x) := by
  induction coeff generalizing x with
  | nil => simp only [eval, List.map_nil, map_zero]
  | cons c cs ih =>
      simp only [eval, List.map_cons]
      rw [map_add, map_mul, ih (x * x), map_mul]

#print axioms eval_map

end SparseLinearized
