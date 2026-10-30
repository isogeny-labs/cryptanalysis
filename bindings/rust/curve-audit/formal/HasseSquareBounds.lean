import HasseUnique

namespace CurveAudit

/-- The integer square checks used by the certificate imply that the sum of
    two nonnegative deviations is strictly smaller than the subgroup order.
    This avoids choosing or formalizing a square root. -/
theorem squared_deviations_have_short_sum
    (p r d₁ d₂ : Nat)
    (hd₁ : d₁ * d₁ ≤ 4 * p)
    (hd₂ : d₂ * d₂ ≤ 4 * p)
    (hr : 16 * p < r * r) : d₁ + d₂ < r := by
  have two_deviation_lt (d : Nat) (hd : d * d ≤ 4 * p) : 2 * d < r := by
    have hfour : (2 * d) * (2 * d) ≤ 16 * p := by
      calc
        (2 * d) * (2 * d) = 4 * (d * d) := by
          calc
            (2 * d) * (2 * d) = (2 * 2) * (d * d) := by ac_rfl
            _ = 4 * (d * d) := by rfl
        _ ≤ 4 * (4 * p) := Nat.mul_le_mul_left 4 hd
        _ = 16 * p := by
          calc
            4 * (4 * p) = (4 * 4) * p := by ac_rfl
            _ = 16 * p := by rfl
    by_cases hlt : 2 * d < r
    · exact hlt
    · have hle : r ≤ 2 * d := by omega
      have hsquare : r * r ≤ (2 * d) * (2 * d) := Nat.mul_self_le_mul_self hle
      omega
  have h₁ := two_deviation_lt d₁ hd₁
  have h₂ := two_deviation_lt d₂ hd₂
  omega

/-- If both candidate and actual cardinality have squared deviations at most
    `4*p` from the same center, and `r² > 16*p`, they cannot be distinct
    multiples of `r`. The center bounds and divisibility remain premises. -/
theorem unique_multiple_from_squared_center_bounds
    (p r center n m d₁ d₂ k l : Nat)
    (hd₁ : d₁ * d₁ ≤ 4 * p)
    (hd₂ : d₂ * d₂ ≤ 4 * p)
    (hr : 16 * p < r * r)
    (hn : n = k * r) (hm : m = l * r)
    (hnLower : center ≤ n + d₁) (hnUpper : n ≤ center + d₁)
    (hmLower : center ≤ m + d₂) (hmUpper : m ≤ center + d₂) : n = m := by
  have hwidth := squared_deviations_have_short_sum p r d₁ d₂ hd₁ hd₂ hr
  apply unique_multiple_in_short_interval r (d₁ + d₂) n m k l hwidth hn hm
  · omega
  · omega

/-- Match the Rust certificate's nonnegative absolute-difference calculation. -/
def unsignedDelta (n center : Nat) : Nat :=
  if center ≤ n then n - center else center - n

theorem unsignedDelta_center_bounds (n center : Nat) :
    center ≤ n + unsignedDelta n center ∧
    n ≤ center + unsignedDelta n center := by
  by_cases h : center ≤ n
  · simp only [unsignedDelta, if_pos h]
    constructor <;> omega
  · simp only [unsignedDelta, if_neg h]
    constructor <;> omega

/-- Arithmetic uniqueness using the certificate's exact predicates: the
    center is `p+1`, both unsigned deviations square to at most `4p`, and
    `r² > 16p`. Exact curve-order divisibility and the actual curve's Hasse
    bound are still external premises. -/
theorem unique_multiple_from_hasse_squared_checks
    (p r n m k l : Nat)
    (hn : n = k * r) (hm : m = l * r)
    (hnSquare : unsignedDelta n (p + 1) * unsignedDelta n (p + 1) ≤ 4 * p)
    (hmSquare : unsignedDelta m (p + 1) * unsignedDelta m (p + 1) ≤ 4 * p)
    (hrSquare : 16 * p < r * r) : n = m := by
  exact unique_multiple_from_squared_center_bounds p r (p + 1) n m
    (unsignedDelta n (p + 1)) (unsignedDelta m (p + 1)) k l
    hnSquare hmSquare hrSquare hn hm
    (unsignedDelta_center_bounds n (p + 1)).1
    (unsignedDelta_center_bounds n (p + 1)).2
    (unsignedDelta_center_bounds m (p + 1)).1
    (unsignedDelta_center_bounds m (p + 1)).2

#print axioms squared_deviations_have_short_sum
#print axioms unique_multiple_from_squared_center_bounds
#print axioms unsignedDelta_center_bounds
#print axioms unique_multiple_from_hasse_squared_checks

end CurveAudit
