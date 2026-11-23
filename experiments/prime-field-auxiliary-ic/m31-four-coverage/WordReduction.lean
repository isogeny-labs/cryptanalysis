import Mathlib.Tactic
import Std.Tactic.BVDecide

namespace M31FourCoverage.WordReduction

private abbrev p : ℕ := 2147483647
private abbrev radix : ℕ := 2147483648

/-- The high and low parts fit a 32-bit sum and need at most one subtraction.
The bound includes a product of canonical operands plus two spare moduli. -/
theorem fold_correct (t : ℕ) (ht : t ≤ (p-1)^2 + 2*p) :
    let s := t/radix + t%radix
    s < 2^32 ∧ (if s ≥ p then s-p else s) = t%p := by
  dsimp only
  have hq : t/radix < p := (Nat.div_lt_iff_lt_mul (by decide)).mpr
    (lt_of_le_of_lt ht (by decide))
  have hr := Nat.mod_lt t (show 0 < radix by decide)
  have hs : t/radix + t%radix < 2*p := by
    have eqn : radix = p+1 := by decide
    omega
  have hmod : t % p = (t/radix + t%radix) % p := by
    conv_lhs => rw [← Nat.div_add_mod t radix]
    simp only [Nat.add_mod, Nat.mul_mod, show radix % p = 1 by decide, one_mul,
      Nat.mod_mod]
  constructor
  · exact lt_trans hs (by decide)
  · rw [hmod]
    split_ifs with h
    · have hsmall : t/radix+t%radix-p < p := by omega
      exact ((Nat.mod_eq_sub_mod h).trans (Nat.mod_eq_of_lt hsmall)).symm
    · exact (Nat.mod_eq_of_lt (by omega)).symm

theorem accumulator_bound (a b c : ℕ) (ha : a < p) (hb : b < p) (hc : c ≤ 2*p) :
    a*b+c ≤ (p-1)^2+2*p := by
  rw [pow_two]
  exact Nat.add_le_add (Nat.mul_le_mul (by omega) (by omega)) hc

/-- The additive offset implements two field subtractions without signed words. -/
theorem offset_correct (t x y : ℕ) (hx : x < p) (hy : y < p) :
    (t+(2*p-x-y)+x+y)%p = t%p := by
  have he : t+(2*p-x-y)+x+y = t+2*p := by omega
  rw [he]
  simp

theorem ordinate_offset (t y : ℕ) (hy : y < p) :
    (t+(p-y)+y)%p = t%p := by
  have he : t+(p-y)+y = t+p := by omega
  rw [he]
  simp

theorem accumulator_fits_uint64 : (p-1)^2+2*p < 2^64 := by decide

/-- The Rust M31 affine fast path agrees with reducing the square and
then subtracting each canonical coordinate separately. -/
theorem rust_abscissa (s x y : ℕ) (hs : s < p) (hx : x < p) (hy : y < p) :
    let t := s*s+(2*p-x-y)
    let q := t/radix+t%radix
    (if q ≥ p then q-p else q) = ((s*s%p + (p-x))%p + (p-y))%p := by
  dsimp only
  have bound := accumulator_bound s s (2*p-x-y) hs hs (by omega)
  rw [(fold_correct _ bound).2]
  rw [Nat.mod_add_mod, Nat.add_assoc, Nat.mod_add_mod]
  congr 1
  omega

/-- Both variants operate on actual wrapping 32-bit words. -/
theorem add_carry (a b : BitVec 32) (ha : a < 2147483647) (hb : b ≤ 2147483647) :
    let s := a+b
    ((s + ((s+1) >>> 31)) &&& 2147483647) =
      (if s ≥ 2147483647 then s-2147483647 else s) := by
  bv_decide

theorem sub_borrow (a b : BitVec 32) (ha : a < 2147483647) (hb : b < 2147483647) :
    let d := a-b
    ((d - (d >>> 31)) &&& 2147483647) =
      (if a ≥ b then a-b else 2147483647-(b-a)) := by
  bv_decide

end M31FourCoverage.WordReduction
