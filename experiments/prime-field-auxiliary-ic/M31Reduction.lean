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

/-- One Mersenne fold on an arbitrary unsigned word. -/
def foldWord (x : BitVec 64) : BitVec 64 :=
  (x >>> 31) + (x &&& 2147483647)

private abbrev foldNat (x : Nat) := x / 2147483648 + x % 2147483648

private theorem foldWord_toNat (x : BitVec 64) :
    (foldWord x).toNat = foldNat x.toNat := by
  have hi : (x >>> 31).toNat = x.toNat / 2147483648 := by
    rw [BitVec.toNat_ushiftRight, Nat.shiftRight_eq_div_pow]
  have lo : (x &&& 2147483647).toNat = x.toNat % 2147483648 := by
    rw [BitVec.toNat_and]
    exact Nat.and_two_pow_sub_one_eq_mod x.toNat 31
  have hx := x.isLt
  unfold foldWord foldNat
  rw [BitVec.toNat_add_of_lt, hi, lo]
  rw [hi, lo]
  omega

private theorem fold_mod (x : Nat) : foldNat x % modulus = x % modulus := by
  have h := Nat.mod_add_div x 2147483648
  unfold foldNat modulus
  omega

/-- Canonicalize any 64-bit accumulator, including values larger than a field product. -/
def reduceWord (x : BitVec 64) : BitVec 64 :=
  let s := foldWord (foldWord x)
  if 2147483647 ≤ s then s - 2147483647 else s

theorem reduceWord_correct (x : BitVec 64) :
    (reduceWord x).toNat = x.toNat % modulus := by
  let s := foldWord (foldWord x)
  have hs : s.toNat = foldNat (foldNat x.toNat) := by
    dsimp only [s]
    rw [foldWord_toNat, foldWord_toNat]
  have hx := x.isLt
  have small : s.toNat < 2 * modulus := by
    unfold foldNat at hs
    unfold modulus
    omega
  have congr : s.toNat % modulus = x.toNat % modulus := by
    rw [hs, fold_mod, fold_mod]
  rw [← congr]
  change (if (2147483647 : BitVec 64) ≤ s then s - 2147483647 else s).toNat = _
  split
  next h =>
    rw [BitVec.toNat_sub_of_le h]
    change 2147483647 ≤ s.toNat at h
    change s.toNat - 2147483647 = s.toNat % 2147483647
    unfold modulus at small
    omega
  next h =>
    change ¬ 2147483647 ≤ s.toNat at h
    exact (Nat.mod_eq_of_lt (by unfold modulus; omega)).symm

private theorem product_bound {a b : Nat} (ha : a < modulus) (hb : b < modulus) :
    a*b ≤ 2147483646 * 2147483646 :=
  Nat.mul_le_mul (by unfold modulus at ha; omega) (by unfold modulus at hb; omega)

/-- Four products of canonical representatives fit in one unsigned accumulator. -/
theorem four_products_fit (a b c d e f g h : Fin modulus) :
    a.val*b.val + c.val*d.val + e.val*f.val + g.val*h.val < 2^64 := by
  have h₁ := product_bound a.isLt b.isLt
  have h₂ := product_bound c.isLt d.isLt
  have h₃ := product_bound e.isLt f.isLt
  have h₄ := product_bound g.isLt h.isLt
  omega

/-- Word multiplication and accumulation are exact before the fused reduction. -/
theorem sum_products_correct (a b c d : BitVec 64)
    (ha : a.toNat < modulus) (hb : b.toNat < modulus)
    (hc : c.toNat < modulus) (hd : d.toNat < modulus) :
    (reduceWord (a*b+c*d)).toNat = (a.toNat*b.toNat+c.toNat*d.toNat) % modulus := by
  have h₁ := product_bound ha hb
  have h₂ := product_bound hc hd
  have ab : (a*b).toNat = a.toNat*b.toNat := BitVec.toNat_mul_of_lt (by omega)
  have cd : (c*d).toNat = c.toNat*d.toNat := BitVec.toNat_mul_of_lt (by omega)
  rw [reduceWord_correct, BitVec.toNat_add_of_lt, ab, cd]
  rw [ab, cd]
  omega

/-- The high bits wrapped into the low end of a 31-bit rotation do not
overlap the shifted low bits. -/
private theorem rotate_toNat (x : BitVec 31) (k : Nat) (hk : k < 31) :
    (x.rotateLeft k).toNat =
      2^k * (x.toNat % 2^(31-k)) + x.toNat / 2^(31-k) := by
  have splitPow : 2^31 = 2^(31-k) * 2^k := by
    rw [← Nat.pow_add]
    congr 1
    omega
  have hi : x.toNat / 2^(31-k) < 2^k := by
    apply (Nat.div_lt_iff_lt_mul (Nat.two_pow_pos _)).mpr
    rw [Nat.mul_comm, ← splitPow]
    exact x.isLt
  rw [BitVec.toNat_rotateLeft, Nat.mod_eq_of_lt hk, Nat.shiftLeft_eq,
    Nat.shiftRight_eq_div_pow, splitPow, Nat.mul_mod_mul_right,
    Nat.mul_comm (x.toNat % _), ← Nat.two_pow_add_eq_or_of_lt hi]

/-- A cyclic left rotation multiplies a canonical M31 residue by a power of two.
The canonicality assumption excludes the all-ones representation of zero. -/
theorem rotate_correct (x : BitVec 31) (k : Nat) (hk : k < 31)
    (hx : x.toNat < modulus) :
    (x.rotateLeft k).toNat = (2^k * x.toNat) % modulus := by
  rw [rotate_toNat x k hk]
  have h := Nat.mod_add_div x.toNat (2^(31-k))
  unfold modulus at *
  -- Each shift fixes the divisor, so the remaining identity is linear.
  iterate 31
    cases k <;> first | omega | rename_i k

/-- Negate the rotated canonical representative, retaining zero as zero. -/
theorem negative_rotate_correct (x : BitVec 31) (k : Nat) (hk : k < 31)
    (hx : x.toNat < modulus) :
    (if x.toNat = 0 then 0 else modulus - (x.rotateLeft k).toNat) =
      ((modulus - 2^k) * x.toNat) % modulus := by
  rw [rotate_toNat x k hk]
  have h := Nat.mod_add_div x.toNat (2^(31-k))
  unfold modulus at *
  split
  · simp_all
  · iterate 31
      cases k <;> first | omega | rename_i k

end M31Reduction
