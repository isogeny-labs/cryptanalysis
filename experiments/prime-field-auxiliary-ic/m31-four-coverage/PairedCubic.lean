import Mathlib.Tactic

namespace M31PairedCubic

def rhs {K : Type*} [CommRing K] (a b x : K) := x^3 + a*x + b

theorem opposite_rhs {K : Type*} [CommRing K] (a b x : K) :
    rhs a b (-x) = 2*b - rhs a b x := by
  unfold rhs
  ring

theorem valid_opposite {K : Type*} [CommRing K] (a b x y : K) :
    y*y = 2*b - rhs a b x ↔ y*y = rhs a b (-x) := by rw [opposite_rhs]

def pack (x y : Nat) := (x <<< 31) ||| y

private theorem packed_value (x y : Nat) (hy : y < 2147483647) :
    pack x y = x*2147483648 + y := by
  unfold pack
  rw [← Nat.shiftLeft_add_eq_or_of_lt (show y < 2^31 by omega), Nat.shiftLeft_eq]

theorem fits (x y : Nat) (hx : x < 2147483647) (hy : y < 2147483647) :
    pack x y < 2^62 := by rw [packed_value x y hy]; omega

theorem unpack (x y : Nat) (hy : y < 2147483647) :
    (pack x y >>> 31 = x) ∧ (pack x y &&& 2147483647 = y) := by
  rw [packed_value x y hy, Nat.shiftRight_eq_div_pow,
    show 2147483647 = 2^31-1 by decide, Nat.and_two_pow_sub_one_eq_mod]
  omega

theorem unsigned_order (x y u v : Nat) (hy : y < 2147483647) (hv : v < 2147483647) :
    pack x y < pack u v ↔ x < u ∨ (x = u ∧ y < v) := by
  rw [packed_value x y hy, packed_value u v hv]
  omega

end M31PairedCubic
