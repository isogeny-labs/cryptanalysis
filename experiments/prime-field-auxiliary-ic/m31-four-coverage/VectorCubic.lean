import Mathlib.Tactic
import Std.Tactic.BVDecide

namespace M31VectorCubic

abbrev p : Nat := 2147483647
abbrev radix : Nat := 2147483648

def fold (z : Nat) := z % radix + z / radix
def reduce (s : Nat) := if s < p then s else s-p

theorem reduce_exact (s : Nat) (h : s < 2*p) : reduce s = s % p := by
  unfold reduce p at *
  split <;> omega

theorem mul_exact (a b : Nat) (ha : a < p) (hb : b < p) :
    2*(a*b) < 2^63 ∧ reduce (fold (a*b)) = (a*b) % p := by
  have bound := Nat.mul_le_mul (show a ≤ p-1 by omega) (show b ≤ p-1 by omega)
  have fits : fold (a*b) < 2*p := by unfold fold radix p at *; omega
  have dec := Nat.mod_add_div (a*b) radix
  have split : a*b = fold (a*b) + p*((a*b)/radix) := by unfold fold radix p at *; omega
  constructor
  · norm_num [p] at bound ⊢
    omega
  · rw [reduce_exact _ fits]
    conv_rhs => rw [split]
    simp

/-- Unsigned minimum selects a single modular subtraction, including the underflow case. -/
theorem lane_reduce (s : BitVec 32) (h : s < 4294967294#32) :
    (if s ≤ s-2147483647 then s else s-2147483647) = if s < 2147483647 then s else s-2147483647 := by
  bv_decide

theorem factored_values {R : Type*} [CommRing R] (x b : R) :
    (b + x*(x*x+2), b - x*(x*x+2)) = (x^3+2*x+b, (-x)^3+2*(-x)+b) := by
  congr 1 <;> ring

/-- Adding singleton lane weights produces the same four flags without carries. -/
theorem horizontal_flags (a b c d : Bool) :
    let weight := fun (v : Bool) (n : BitVec 32) => if v then n else 0
    let m := weight a 1 + weight b 2 + weight c 4 + weight d 8
    (m.getLsbD 0, m.getLsbD 1, m.getLsbD 2, m.getLsbD 3) = (a,b,c,d) ∧ m < 16 := by
  cases a <;> cases b <;> cases c <;> cases d <;> decide

end M31VectorCubic
