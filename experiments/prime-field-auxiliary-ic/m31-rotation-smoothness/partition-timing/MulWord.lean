import Mathlib.Data.Nat.Bitwise

namespace M31CensusWord

abbrev modulus : Nat := 2147483647

/-- In bench.cpp the addition is 64-bit, the assignment to r narrows to
32 bits, and the comparison and subtraction then use the narrow word. -/
def reduceProduct (z : BitVec 64) : BitVec 32 :=
  let r := ((z &&& (2147483647 : BitVec 64)) + (z >>> 31)).setWidth 32
  if r ≥ 2147483647 then r - 2147483647 else r

theorem fold_correct (z : BitVec 64) (hz : z.toNat < 2^62 - 1) :
    (reduceProduct z).toNat = z.toNat % modulus := by
  let s := (z &&& (2147483647 : BitVec 64)) + (z >>> 31)
  have hi : (z >>> 31).toNat = z.toNat / 2147483648 := by
    rw [BitVec.toNat_ushiftRight, Nat.shiftRight_eq_div_pow]
  have lo : (z &&& (2147483647 : BitVec 64)).toNat = z.toNat % 2147483648 := by
    rw [BitVec.toNat_and]
    exact Nat.and_two_pow_sub_one_eq_mod z.toNat 31
  have splitZ := Nat.mod_add_div z.toNat 2147483648
  have small : z.toNat % 2147483648 + z.toNat / 2147483648 < 2*modulus := by
    unfold modulus
    omega
  have hs : s.toNat = z.toNat % 2147483648 + z.toNat / 2147483648 := by
    dsimp only [s]
    rw [BitVec.toNat_add_of_lt, lo, hi]
    rw [lo, hi]
    unfold modulus at small
    omega
  have h32 : (s.setWidth 32).toNat = s.toNat := by
    rw [BitVec.toNat_setWidth, Nat.mod_eq_of_lt]
    unfold modulus at small
    omega
  have hmod : z.toNat % modulus = s.toNat % modulus := by
    unfold modulus
    omega
  rw [hmod]
  change (if (s.setWidth 32) ≥ 2147483647 then s.setWidth 32 - 2147483647 else s.setWidth 32).toNat = _
  split
  next h =>
    rw [BitVec.toNat_sub_of_le h, h32]
    change 2147483647 ≤ (s.setWidth 32).toNat at h
    change s.toNat - 2147483647 = s.toNat % 2147483647
    unfold modulus at small
    omega
  next h =>
    change ¬ 2147483647 ≤ (s.setWidth 32).toNat at h
    rw [h32]
    exact (Nat.mod_eq_of_lt (by unfold modulus; omega)).symm

theorem first_failure :
    (reduceProduct 4611686018427387903).toNat = modulus ∧ (2^62-1 : Nat) % modulus = 0 := by
  constructor
  · change (reduceProduct 4611686018427387903).toNat = 2147483647
    apply congrArg BitVec.toNat (a₂ := (2147483647 : BitVec 32))
    unfold reduceProduct
    bv_decide
  · rfl

theorem mul_correct (a b : BitVec 32) (ha : a.toNat < modulus) (hb : b.toNat < modulus) :
    (reduceProduct (a.setWidth 64 * b.setWidth 64)).toNat =
      (a.toNat * b.toNat) % modulus := by
  have bound := Nat.mul_le_mul (show a.toNat ≤ 2147483646 by unfold modulus at ha; omega)
    (show b.toNat ≤ 2147483646 by unfold modulus at hb; omega)
  have hprod : (a.setWidth 64 * b.setWidth 64).toNat = a.toNat * b.toNat := by
    rw [BitVec.toNat_mul_of_lt] <;> simp only [BitVec.toNat_setWidth_of_le (by decide : 32 ≤ 64)]
    omega
  rw [fold_correct _ (by rw [hprod]; omega), hprod]

def pack (key : BitVec 32) (side : Bool) : BitVec 32 :=
  2 * key + (if side then 1 else 0)

private theorem pack_nat (x : BitVec 32) (a : Bool) (hx : x < 2147483647) :
    (pack x a).toNat = Nat.bit a x.toNat := by
  change x.toNat < 2147483647 at hx
  cases a <;> simp [pack, Nat.bit, BitVec.toNat_add, BitVec.toNat_mul] <;> omega

theorem pair_test (x y : BitVec 32) (a b : Bool)
    (hx : x < 2147483647) (hy : y < 2147483647) :
    (pack x a ^^^ pack y b = 1) ↔ (x = y ∧ a ≠ b) := by
  rw [← BitVec.toNat_inj, BitVec.toNat_xor, pack_nat x a hx, pack_nat y b hy, Nat.xor_bit]
  change Nat.bit (a != b) (x.toNat ^^^ y.toNat) = 1 ↔ _
  rw [← BitVec.toNat_inj, ← Nat.xor_eq_zero_iff]
  cases a <;> cases b <;> simp [Nat.bit]

end M31CensusWord
