import Std

namespace FixtureLift

abbrev p := 2147483647
abbrev radix := 2147483648

/-- The fused right-hand side uses a canonical x² mod p. -/
theorem rhs_bound (x xx : Nat) (hx : x < p) (hxx : xx < p) :
    xx*x + 2*x + 14 ≤ p*p+13 := by
  have h := Nat.mul_le_mul (show xx ≤ 2147483646 by simp only [p] at *; omega)
    (show x ≤ 2147483646 by simp only [p] at *; omega)
  simp only [p] at *
  omega

/-- One fold fits in a u32. One conditional subtraction then suffices. -/
theorem fold_correct (t : Nat) (bound : t ≤ p*p+13) :
    let f := t % radix + t / radix
    t < 2^64 ∧ f < 2^32 ∧ (if p ≤ f then f-p else f) = t % p := by
  have d := Nat.mod_add_div t radix
  have lo := Nat.mod_lt t (by decide : 0 < radix)
  have hi : t / radix ≤ 2147483646 := by simp only [p,radix] at *; omega
  have eq : t = (t / radix)*p + (t%radix + t/radix) := by simp only [p,radix] at *; omega
  have modEq : t % p = (t%radix + t/radix)%p := by
    conv => lhs; rw [eq]
    simp [Nat.add_mod]
  dsimp
  rw [modEq]
  split <;> simp only [p,radix] at * <;> omega

open Lean.Grind
variable {F : Type} [CommRing F]
def iterateSquare (a : F) : Nat → F
  | 0 => a
  | n+1 => let t := iterateSquare a n; t*t

theorem squarePower (a : F) (n : Nat) : iterateSquare a n = a^(2^n) := by
  induction n with
  | zero => simp [iterateSquare]; grind
  | succ n ih =>
    simp only [iterateSquare, ih, Nat.pow_succ]
    rw [show 2^n*2 = 2^n+2^n by omega, Semiring.pow_add]

theorem liftExponent (a : F) : iterateSquare a 29 = a^((p+1)/4) := squarePower a 29

#print axioms fold_correct
#print axioms liftExponent
end FixtureLift
