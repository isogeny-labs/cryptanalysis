import Mathlib

namespace M31Chain

/-- At most k further concatenations of already constructed all-one blocks.
The largest constructed length is at the front. -/
def reaches (goal : Nat) : Nat → List Nat → Bool
  | 0, xs => xs.contains goal
  | k+1, xs => xs.contains goal || xs.any fun a => xs.any fun b =>
      let c := a+b
      xs.head! < c && c ≤ goal && reaches goal k (c :: xs)

set_option maxRecDepth 10000 in
set_option maxHeartbeats 0 in
theorem six_insufficient : reaches 29 6 [1] = false := by native_decide

set_option maxRecDepth 10000 in
set_option maxHeartbeats 0 in
theorem seven_suffice : reaches 29 7 [1] = true := by native_decide

/-- A block of b one bits may be appended to one of a bits. -/
theorem appendExponent (a b : Nat) :
    (2^a-1)*2^b + (2^b-1) = 2^(a+b)-1 := by
  rw [pow_add, Nat.sub_one_mul]
  have ha : 1 ≤ 2^a := Nat.one_le_two_pow
  have hb : 1 ≤ 2^b := Nat.one_le_two_pow
  have hc : 2^b ≤ 2^a * 2^b := by simpa using Nat.mul_le_mul_right (2^b) ha
  omega

example : (2^29-1)*4+1 = (2^31-1)-2 := by decide

end M31Chain
