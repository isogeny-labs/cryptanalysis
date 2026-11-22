import Mathlib

namespace M31Rotate
theorem rotateWord (x : ℕ) (hx : x < 2147483647) :
    2 * (x % 2^30) + x / 2^30 = (2*x) % 2147483647 := by omega

example : (2^31 : ℕ) % 2147483647 = 1 := by decide
example : (List.range 30).all (fun i => (2^(i+1) : ℕ) % 2147483647 != 1) := by decide
end M31Rotate
