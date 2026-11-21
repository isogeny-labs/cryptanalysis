import Std

namespace M31Reduction

abbrev modulus : Nat := 2147483647

/-- Reduce the product of two canonical field representatives. -/
def mul (a b : BitVec 64) : BitVec 64 :=
  let x := a * b
  let s := (x >>> 31) + (x &&& 2147483647)
  if 2147483647 ≤ s then s - 2147483647 else s

theorem mul_correct (a b : BitVec 64) (ha : a.toNat < modulus)
    (hb : b.toNat < modulus) : (mul a b).toNat = (a.toNat * b.toNat) % modulus := by
  let x := a * b
  let s := (x >>> 31) + (x &&& 2147483647)
  have bound : a.toNat * b.toNat ≤ 2147483646 * 2147483646 :=
    Nat.mul_le_mul (by unfold modulus at ha; omega) (by unfold modulus at hb; omega)
  have prod : x.toNat = a.toNat * b.toNat := BitVec.toNat_mul_of_lt (by omega)
  have high : (x >>> 31).toNat = x.toNat / 2147483648 := by
    rw [BitVec.toNat_ushiftRight, Nat.shiftRight_eq_div_pow]
  have low : (x &&& 2147483647).toNat = x.toNat % 2147483648 := by
    rw [BitVec.toNat_and]
    exact Nat.and_two_pow_sub_one_eq_mod x.toNat 31
  have folded : s.toNat = x.toNat / 2147483648 + x.toNat % 2147483648 := by
    dsimp only [s]
    rw [BitVec.toNat_add_of_lt, high, low]
    rw [high, low]; omega
  have eqn := Nat.mod_add_div x.toNat 2147483648
  have decomp : x.toNat = (x.toNat / 2147483648)*modulus + s.toNat := by
    unfold modulus; omega
  have congr : x.toNat % modulus = s.toNat % modulus := calc
    _ = ((x.toNat / 2147483648)*modulus + s.toNat) % modulus := congrArg (· % modulus) decomp
    _ = _ := by simp [Nat.add_mod]
  rw [← prod, congr]
  change (if (2147483647 : BitVec 64) ≤ s then s - 2147483647 else s).toNat = _
  split
  next h =>
    rw [BitVec.toNat_sub_of_le h]
    change s.toNat - 2147483647 = s.toNat % 2147483647
    change 2147483647 ≤ s.toNat at h
    omega
  next h =>
    change ¬ 2147483647 ≤ s.toNat at h
    exact (Nat.mod_eq_of_lt (by unfold modulus; omega)).symm

end M31Reduction
