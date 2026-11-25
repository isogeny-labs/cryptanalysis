import Mathlib

namespace M31Rotate
theorem rotateWord (x : ℕ) (hx : x < 2147483647) :
    2 * (x % 2^30) + x / 2^30 = (2*x) % 2147483647 := by omega

example : (2^31 : ℕ) % 2147483647 = 1 := by decide
example : (List.range 30).all (fun i => (2^(i+1) : ℕ) % 2147483647 != 1) := by decide
/-- The d-th power in lane j is obtained by rotating the initial power by
d*j places, reducing the shift modulo the word width. -/
theorem orbitPower (v : ZMod 2147483647) (j d : ℕ) :
    ((2 : ZMod 2147483647)^j * v)^d = 2^((j*d)%31) * v^d := by
  rw [mul_pow, ← pow_mul]
  congr 1
  conv_lhs => rw [← Nat.mod_add_div (j*d) 31, pow_add, pow_mul]
  rw [show (2 : ZMod 2147483647)^31 = 1 by decide, one_pow, mul_one]

end M31Rotate
