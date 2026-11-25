import Mathlib.Tactic

namespace M31Lane
abbrev Word := BitVec 32
abbrev p : ℕ := 2147483647

/-- Canonical unsigned inputs have the same signed interpretation. -/
theorem signed_input (x : Word) (hx : x.toNat < p) : x.toInt = (x.toNat : ℤ) := by
  simp only [BitVec.toInt]
  split <;> simp_all [p]
  omega

/-- Doubling the product stays inside the signed 64-bit saturation range. -/
theorem no_sat (a b : ℕ) (ha : a < p) (hb : b < p) :
    2*(a*b) < 2^63 := by
  unfold p at ha hb
  have h := Nat.mul_le_mul (show a ≤ 2147483646 by omega)
    (show b ≤ 2147483646 by omega)
  omega

def low (x y : Word) := (x*y) &&& (2147483647 : Word)
def high (x y : Word) : Word := BitVec.ofNat 32
  (min (2*(x.toNat*y.toNat)) (2^63-1) / 2^32)

theorem low_spec (x y : Word) : (low x y).toNat = (x.toNat*y.toNat)%2^31 := by
  rw [low, BitVec.toNat_and, BitVec.toNat_mul]
  change (_ &&& (2^31-1)) = _
  rw [Nat.and_two_pow_sub_one_eq_mod, Nat.mod_mod_of_dvd _ (by decide : 2^31 ∣ 2^32)]

theorem lane (x y : Word) (hx : x.toNat < p) (hy : y.toNat < p) :
    let f := low x y + high x y
    min f.toNat ((f - (2147483647 : Word)).toNat) = (x.toNat*y.toNat)%p := by
  have h := no_sat _ _ hx hy
  have hi : (high x y).toNat = (x.toNat*y.toNat)/2^31 := by
    simp only [high, BitVec.toNat_ofNat]
    rw [min_eq_left (by omega)]
    omega
  let t := x.toNat*y.toNat
  let r := t%2147483648 + t/2147483648
  have hb : t ≤ 2147483646 * 2147483646 := by
    unfold p at hx hy
    exact Nat.mul_le_mul (by omega) (by omega)
  have hr : r < 4294967294 := by dsimp [r]; omega
  have hf : (low x y + high x y).toNat = r := by
    rw [BitVec.toNat_add,low_spec,hi]
    exact Nat.mod_eq_of_lt (show r < 4294967296 by omega)
  dsimp only
  rw [BitVec.toNat_sub,hf]
  change min r ((2147483649+r)%4294967296) = t%2147483647
  have hc : min r ((2147483649+r)%4294967296) =
      (if r < 2147483647 then r else r-2147483647) := by split <;> omega
  rw [hc]
  dsimp [r]
  split <;> omega
end M31Lane

/-- Folding the high bit also admits noncanonical uint32 inputs. -/
theorem m31_input_fold (x : ℕ) (hx : x < 2^32) :
    let f := x % 2^31 + x / 2^31
    min f ((2147483649 + f) % 4294967296) = x % 2147483647 := by
  dsimp only
  have hq : x / 2^31 = 0 ∨ x / 2^31 = 1 := by omega
  have hp : x / 2147483647 = 0 ∨ x / 2147483647 = 1 ∨ x / 2147483647 = 2 := by omega
  rw [Nat.min_def]
  rcases hq with hq | hq <;> rcases hp with hp | hp | hp <;> split <;> omega
