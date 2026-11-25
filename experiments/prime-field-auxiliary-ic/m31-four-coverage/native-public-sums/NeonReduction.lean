import Std

namespace M31.Neon

/-- Natural-number model of one unsigned 32-bit lane after widening multiplication.
The low half narrows to 32 bits before the 31-bit mask. -/
def reduceLane (z : Nat) : Nat :=
  let low := z % 4294967296 % 2147483648
  let high := (z / 2147483648) % 4294967296
  let sum := (low + high) % 4294967296
  min sum ((sum + 4294967296 - 2147483647) % 4294967296)

theorem lane_correct (z : Nat) (hz : z ≤ 2147483646 * 2147483646) :
    reduceLane z = z % 2147483647 := by
  let q := z / 2147483648
  let r := z % 2147483648
  have split : z = q * 2147483648 + r := by dsimp [q,r]; omega
  have hq : q ≤ 2147483644 := by dsimp [q]; omega
  have hr : r < 2147483648 := Nat.mod_lt _ (by decide)
  have hlow : z % 4294967296 % 2147483648 = r := by dsimp [r]; omega
  have hh : q % 4294967296 = q := Nat.mod_eq_of_lt (by omega)
  have hs : (r + q) % 4294967296 = r + q := Nat.mod_eq_of_lt (by omega)
  change min ((z % 4294967296 % 2147483648 + q % 4294967296) % 4294967296) _ = _
  rw [hlow, hh, hs]
  by_cases small : r + q < 2147483647
  · rw [Nat.min_eq_left (by omega)]
    omega
  · rw [Nat.min_eq_right (by omega)]
    omega

theorem product_correct (a b : Nat) (ha : a < 2147483647) (hb : b < 2147483647) :
    reduceLane (a*b) = a*b % 2147483647 :=
  lane_correct _ (Nat.mul_le_mul (by omega) (by omega))

end M31.Neon
