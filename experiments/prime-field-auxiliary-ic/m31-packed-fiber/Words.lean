import Std.Tactic.BVDecide
import Init.Data.BitVec.Lemmas

namespace M31PackedFiber.Words

abbrev p : Nat := 2147483647
abbrev w : BitVec 32 := 2147483647

def add (x y : BitVec 32) := if x+y ≥ w then x+y-w else x+y
def sub (x y : BitVec 32) := if x ≥ y then x-y else w-(y-x)
def mul (x y : BitVec 32) :=
  ((x.setWidth 64 * y.setWidth 64) % (2147483647 : BitVec 64)).setWidth 32

theorem add_spec (x y : BitVec 32) (hx : x.toNat < p) (hy : y.toNat < p) :
    (add x y).toNat = (x.toNat + y.toNat) % p := by
  have hs := BitVec.toNat_add_of_lt (x := x) (y := y) (by unfold p at *; omega)
  unfold add
  split
  next h =>
    rw [BitVec.toNat_sub_of_le h, hs]
    change 2147483647 ≤ (x+y).toNat at h
    rw [hs] at h
    change _ - 2147483647 = _ % 2147483647
    unfold p at hx hy
    omega
  next h =>
    rw [hs]
    change ¬ 2147483647 ≤ (x+y).toNat at h
    rw [hs] at h
    exact (Nat.mod_eq_of_lt (Nat.lt_of_not_ge h)).symm

theorem sub_spec (x y : BitVec 32) (hx : x.toNat < p) (hy : y.toNat < p) :
    (sub x y).toNat = (x.toNat + p - y.toNat) % p := by
  unfold sub
  split
  next h =>
    rw [BitVec.toNat_sub_of_le h]
    change y.toNat ≤ x.toNat at h
    unfold p at *
    omega
  next h =>
    have hxy : x ≤ y := by change x.toNat ≤ y.toNat; change ¬ y.toNat ≤ x.toNat at h; omega
    have hd := BitVec.toNat_sub_of_le hxy
    have hw : y-x ≤ w := by change (y-x).toNat ≤ p; rw [hd]; omega
    rw [BitVec.toNat_sub_of_le hw, hd]
    change ¬ y.toNat ≤ x.toNat at h
    change p - _ = _
    unfold p at *
    omega

theorem mul_spec (x y : BitVec 32) :
    (mul x y).toNat = x.toNat * y.toNat % p := by
  have h := BitVec.toNat_mul_toNat_lt (x := x) (y := y)
  have hx := BitVec.toNat_setWidth_of_le (b := x) (show 32 ≤ 64 by decide)
  have hy := BitVec.toNat_setWidth_of_le (b := y) (show 32 ≤ 64 by decide)
  unfold mul
  rw [BitVec.toNat_setWidth, BitVec.toNat_umod, BitVec.toNat_mul, hx, hy, Nat.mod_eq_of_lt h]
  change (_ % p) % 4294967296 = _
  exact Nat.mod_eq_of_lt (Nat.lt_trans (Nat.mod_lt _ (by decide : 0 < p)) (by decide))

end M31PackedFiber.Words
