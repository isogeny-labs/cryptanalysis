import Mathlib

namespace M31Ffi

/-- All intermediate sums and the folded result fit in the C word sizes. -/
theorem foldBounds (v : ℕ) (h : v ≤ 2147483646^2) :
    v < 2^64 ∧ v % 2147483648 + v / 2147483648 < 2*2147483647 := by
  omega

theorem multiplyFold (a b : ℕ) (ha : a < 2147483647) (hb : b < 2147483647) :
    let v := a*b
    let r := v % 2147483648 + v / 2147483648
    (if r ≥ 2147483647 then r-2147483647 else r) = v % 2147483647 := by
  dsimp only
  let v := a*b
  change (if v%2147483648+v/2147483648 ≥ 2147483647 then _ else _) = v%2147483647
  have h : v ≤ 2147483646^2 := by
    unfold v
    exact (show 2147483646*2147483646 = 2147483646^2 by norm_num) ▸
      Nat.mul_le_mul (by omega : a ≤ 2147483646) (by omega : b ≤ 2147483646)
  have hr := (foldBounds v h).2
  have he : v = (v%2147483648+v/2147483648)+2147483647*(v/2147483648) := by
    have := Nat.mod_add_div v 2147483648
    omega
  conv_rhs => rw [he, Nat.add_mul_mod_self_left]
  split <;> omega

end M31Ffi
