import MulWord

namespace M31CensusWord

def affineOffset (x y : BitVec 32) := (2*2147483647 - x - y : BitVec 32)
def affineInput (s x y : BitVec 32) : BitVec 64 :=
  s.setWidth 64 * s.setWidth 64 + (affineOffset x y).setWidth 64

def narrowFold (z : BitVec 64) : BitVec 32 :=
  let r := (z >>> 31).setWidth 32 + (z.setWidth 32 &&& 2147483647)
  if r ≥ 2147483647 then r - 2147483647 else r

theorem narrow_eq (z : BitVec 64) : narrowFold z = reduceProduct z := by
  unfold narrowFold reduceProduct
  rw [BitVec.setWidth_add _ _ (by decide), BitVec.setWidth_and, BitVec.add_comm]
  rfl

theorem offset_exact (x y : BitVec 32) (hx : x.toNat < modulus) (hy : y.toNat < modulus) :
    (affineOffset x y).toNat = 2*modulus - x.toNat - y.toNat := by
  have h₁ : x ≤ (2*2147483647 : BitVec 32) := by
    change x.toNat ≤ 4294967294
    unfold modulus at hx
    omega
  have h₂ : y ≤ (2*2147483647 : BitVec 32) - x := by
    change y.toNat ≤ ((2*2147483647 : BitVec 32)-x).toNat
    rw [BitVec.toNat_sub_of_le h₁]
    change y.toNat ≤ 4294967294-x.toNat
    unfold modulus at hx hy
    omega
  unfold affineOffset
  rw [BitVec.toNat_sub_of_le h₂, BitVec.toNat_sub_of_le h₁]
  rfl

theorem affine_correct (s x y : BitVec 32)
    (hs : s.toNat < modulus) (hx : x.toNat < modulus) (hy : y.toNat < modulus) :
    (narrowFold (affineInput s x y)).toNat =
      (s.toNat*s.toNat + (2*modulus-x.toNat-y.toNat)) % modulus := by
  have hs' : s.toNat ≤ 2147483646 := by unfold modulus at hs; omega
  have square := Nat.mul_le_mul hs' hs'
  have lift (w : BitVec 32) : (w.setWidth 64).toNat = w.toNat :=
    BitVec.toNat_setWidth_of_le (by decide)
  have sq : (s.setWidth 64 * s.setWidth 64).toNat = s.toNat*s.toNat := by
    rw [BitVec.toNat_mul_of_lt] <;> simp only [lift]
    omega
  have exactInput : (affineInput s x y).toNat = s.toNat*s.toNat+(2*modulus-x.toNat-y.toNat) := by
    unfold affineInput
    rw [BitVec.toNat_add_of_lt] <;> rw [sq,lift,offset_exact _ _ hx hy]
    unfold modulus
    omega
  rw [narrow_eq, fold_correct, exactInput]
  rw [exactInput]
  unfold modulus
  omega

#print axioms affine_correct
end M31CensusWord
