import Mathlib

namespace M31Product

theorem signedHigh (a b : ℕ) (ha : a < 2147483647) (hb : b < 2147483647) :
    2*(a*b) < 2^63 ∧ 2*(a*b)/2^32 = a*b/2^31 := by
  have h := Nat.mul_le_mul (show a ≤ 2147483646 by omega) (show b ≤ 2147483646 by omega)
  constructor <;> omega

theorem unsignedMin (s : ℕ) (hs : s < 2*2147483647) :
    min s ((s+2^32-2147483647)%2^32) = s%2147483647 := by
  rw [min_def]
  split <;> omega

/-- Arithmetic value of one NEON lane on canonical field inputs. -/
def lane (a b : ℕ) : ℕ :=
  let z := a*b
  let s := z % 2^31 + 2*z / 2^32
  min s ((s+2^32-2147483647)%2^32)

theorem lane_eq (a b : ℕ) (ha : a < 2147483647) (hb : b < 2147483647) :
    lane a b = a*b % 2147483647 := by
  unfold lane
  dsimp only
  rw [(signedHigh a b ha hb).2]
  have bound := Nat.mul_le_mul (show a ≤ 2147483646 by omega) (show b ≤ 2147483646 by omega)
  rw [unsignedMin _ (by omega)]
  have h := Nat.mod_add_div (a*b) (2^31)
  let q := a*b / 2^31
  let r := a*b % 2^31
  change (r+q)%2147483647 = (a*b)%2147483647
  have hz : r+q+2147483647*q = a*b := by dsimp [r,q]; omega
  conv_rhs => rw [← hz]
  simp [Nat.add_mod]

end M31Product
