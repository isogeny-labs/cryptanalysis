import Mathlib

namespace M31Reduction

abbrev p : Nat := 2147483647
def fold (x : Nat) := x % 2147483648 + x / 2147483648
def canonical (s : Nat) := if s ≥ p then s-p else s

theorem bits (x : Nat) : (x &&& (2^31-1)) + (x >>> 31) = fold x := by
  rw [Nat.and_two_pow_sub_one_eq_mod, Nat.shiftRight_eq_div_pow]
  rfl

/-- Exact initial interval on which one fold and one subtraction suffice. -/
theorem oneFold (x : Nat) (hx : x < 2^62-1) : canonical (fold x) = x % p := by
  unfold canonical fold p
  norm_num at hx
  split <;> omega

theorem firstFailure : canonical (fold (2^62-1)) ≠ (2^62-1) % p := by decide

theorem singleProduct {a b : Nat} (ha : a < p) (hb : b < p) :
    canonical (fold (a*b)) = (a*b) % p := by
  apply oneFold
  have h := Nat.mul_le_mul (Nat.le_pred_of_lt ha) (Nat.le_pred_of_lt hb)
  exact lt_of_le_of_lt h (by decide)

theorem foldResidue (x : Nat) : fold x % p = x % p := by
  have eq : x = fold x + p * (x / 2147483648) := by unfold fold p; omega
  conv_rhs => rw [eq]
  simp

theorem twoFolds (x : UInt64) :
    canonical (fold (fold x.toNat)) = x.toNat % p := by
  have limit := x.toNat_lt
  have small : fold x.toNat < 2^62-1 := by unfold fold; omega
  rw [oneFold _ small, foldResidue]

theorem accumulatorCapacity :
    4*(p-1)^2 < 2^64 ∧ 2^64 ≤ 5*(p-1)^2 := by decide

theorem twoProductsNeedSecondFold :
    canonical (fold (2*(p-1)^2)) = p+2 ∧ (2*(p-1)^2) % p = 2 := by decide

def wordFold (x : UInt64) : UInt64 := (x &&& (2147483647 : UInt64)) + (x >>> (31 : UInt64))

private theorem wordParts (x : UInt64) :
    wordFold x = x % 2147483648 + x / 2147483648 := by
  unfold wordFold
  bv_decide

theorem wordFoldNat (x : UInt64) : (wordFold x).toNat = fold x.toNat := by
  rw [wordParts, UInt64.toNat_add, UInt64.toNat_mod, UInt64.toNat_div]
  change (fold x.toNat) % 2^64 = fold x.toNat
  apply Nat.mod_eq_of_lt
  have limit := x.toNat_lt
  unfold fold
  omega

/-- The AVX2 lane predicate is signed greater-than p-1 after the two folds. -/
theorem signedTest (x : UInt64) :
    ((wordFold (wordFold x)).toInt64 > 2147483646) ↔
      (2147483647 : UInt64) ≤ wordFold (wordFold x) := by
  unfold wordFold
  bv_decide

def laneReduce (x : UInt64) : UInt64 :=
  let s := wordFold (wordFold x)
  s - (if s.toInt64 > 2147483646 then 2147483647 else 0)

theorem laneCorrect (x : UInt64) : (laneReduce x).toNat = x.toNat % p := by
  rw [← twoFolds x, ← wordFoldNat x, ← wordFoldNat (wordFold x)]
  unfold laneReduce canonical
  simp only [signedTest, UInt64.le_iff_toNat_le]
  change ((wordFold (wordFold x)) -
    (if p ≤ (wordFold (wordFold x)).toNat then 2147483647 else 0)).toNat = _
  split <;> rename_i h
  · have le : (2147483647 : UInt64) ≤ wordFold (wordFold x) := by
      apply UInt64.le_iff_toNat_le.mpr
      exact h
    rw [UInt64.toNat_sub_of_le _ _ le]
    rfl
  · simp

/-- Centered representatives lie between -radius and radius, inclusive. -/
abbrev radius : ℤ := 1073741823
abbrev pairBias : ℤ := 2147483647 * 1073741824

/-- Both signs of the product attain this bound. -/
private theorem centeredProductBound (a b : ℤ) (ha : |a| ≤ radius) (hb : |b| ≤ radius) :
    |a*b| ≤ radius * radius := by
  rw [abs_mul]
  exact mul_le_mul ha hb (abs_nonneg b) (by decide)

/-- A fixed multiple of p moves every two-product sum into the one-fold interval. -/
theorem centeredPair (a b c d : ℤ) (ha : |a| ≤ radius) (hb : |b| ≤ radius)
    (hc : |c| ≤ radius) (hd : |d| ≤ radius) :
    let z := a*b + c*d + pairBias
    0 ≤ z ∧ z < 2^62-1 ∧
      (canonical (fold z.toNat) : ℤ) = (a*b + c*d) % (p : ℤ) := by
  dsimp only
  obtain ⟨lab, uab⟩ := abs_le.mp (centeredProductBound a b ha hb)
  obtain ⟨lcd, ucd⟩ := abs_le.mp (centeredProductBound c d hc hd)
  have lo : 0 ≤ a*b + c*d + pairBias := by unfold radius at *; unfold pairBias; omega
  have hi : a*b + c*d + pairBias < 2^62-1 := by unfold radius at *; unfold pairBias; omega
  refine ⟨lo, hi, ?_⟩
  rw [oneFold _ (by omega), Int.natCast_mod, Int.toNat_of_nonneg lo]
  change (a*b + c*d + 1073741824*(p : ℤ)) % (p : ℤ) = _
  exact Int.add_mul_emod_self_right ..

/-- Three centered products already span more than the whole one-fold interval.
The two extrema are attained by choosing all factors equal to radius and
negating the first factor in each product for the lower extremum. -/
theorem threeCenteredExtrema (bias : ℤ) :
    ¬ (0 ≤ bias - 3*radius^2 ∧ bias + 3*radius^2 < 2^62-1) := by
  unfold radius
  omega

/-- Arithmetic of four independent nonnegative SQDMULH lanes. The low word
comes from ordinary multiplication; unsigned MIN chooses the canonical residue
from the folded sum and its wrapping subtraction. -/
theorem doublingHighLane {a b : Nat} (ha : a < p) (hb : b < p) :
    let x := a*b
    let hi := min (2*x) (2^63-1) / 2^32
    let lo := x % 2^32 % 2^31
    let s := (hi+lo) % 2^32
    min s ((s + 2^32 - p) % 2^32) = x % p := by
  have bound := Nat.mul_le_mul (Nat.le_pred_of_lt ha) (Nat.le_pred_of_lt hb)
  change a*b ≤ 2147483646*2147483646 at bound
  have unclamped : 2*(a*b) ≤ 2^63-1 := by omega
  have hc := singleProduct ha hb
  dsimp only
  rw [min_eq_left unclamped]
  unfold canonical fold p at hc
  unfold p
  split at hc <;> omega

/-- Concatenate two all-one exponent blocks by squaring the first value k times. -/
def joinPowers {G : Type*} [Monoid G] (k : ℕ) (a b : G) : G := a^(2^k) * b

theorem characterChain {G : Type*} [Monoid G] (x : G) :
    let x2 := joinPowers 1 x x
    let x3 := joinPowers 1 x2 x
    let x5 := joinPowers 2 x3 x2
    let x10 := joinPowers 5 x5 x5
    let x15 := joinPowers 5 x10 x5
    joinPowers 15 x15 x15 = x^1073741823 := by
  have step (k m n : ℕ) : joinPowers k (x^m) (x^n) = x^(m*2^k+n) := by
    rw [joinPowers, ← pow_mul, ← pow_add]
  have h2 : joinPowers 1 x x = x^3 := by simpa only [pow_one] using step 1 1 1
  have h3 : joinPowers 1 (x^3) x = x^7 := by simpa only [pow_one] using step 1 3 1
  dsimp only
  simp only [h2, h3, step]
  exact congrArg (x ^ ·) (by decide)

/-- For a nonzero input the archived 30-square equality tests the Euler exponent. -/
theorem squaresCharacter {F : Type*} [Field F] (y : F) (hy : y ≠ 0) :
    y^1073741824 = y ↔ y^1073741823 = 1 := by
  change y^(1073741823 + 1) = y ↔ _
  rw [pow_succ]
  constructor
  · intro h
    exact mul_right_cancel₀ hy (h.trans (one_mul y).symm)
  · intro h
    rw [h, one_mul]

/-- The signed representative produced after squaring remains admissible for
the next doubling-high multiply. Subtracting p unconditionally saves the
canonical comparison inside the squaring loop. -/
def signedSquare (x : ℤ) : ℤ :=
  (x*x) % 2147483648 + (x*x) / 2147483648 - 2147483647

theorem signedSquareInvariant {x : ℤ} (lo : -2147483647 ≤ x) (hi : x ≤ 2147483647) :
    -2147483647 ≤ signedSquare x ∧ signedSquare x < 2147483647 ∧
    2*(x*x) < 2^63 ∧ signedSquare x % 2147483647 = (x*x) % 2147483647 := by
  have lower := mul_self_nonneg x
  have upper : x*x ≤ 2147483647*2147483647 := by
    nlinarith [mul_nonneg (show 0 ≤ 2147483647 + x by omega)
      (show 0 ≤ 2147483647 - x by omega)]
  unfold signedSquare
  omega

end M31Reduction
