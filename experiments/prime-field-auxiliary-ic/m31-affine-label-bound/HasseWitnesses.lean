import Mathlib

namespace M31HasseWitnesses

/-- The index order is b = 7^k for k = 0,...,5 on y² = x³+b,
then a = 1,7 on y² = x³+ax. Each row lists (point order, curve order). -/
def orders : List (ℤ × ℤ) :=
  [(39766506,2147391324), (2147444533,2147444533),
   (715845619,2147536857), (1073787986,2147575972),
   (715840921,2147522763), (27888707,2147430439),
   (2147483648,2147483648), (1073741824,2147483648)]

/-- The two geometric inputs are the squared Hasse bound and divisibility
by the witness order. The remaining cardinality inference is arithmetic. -/
theorem uniqueCount {d expected actual : ℤ} (row : (d, expected) ∈ orders)
    (hasse : (actual - 2147483648)^2 ≤ 4 * 2147483647)
    (divides : d ∣ actual) : actual = expected := by
  have lo : 2147483648 - 92681 ≤ actual := by
    by_contra! h
    have hh : actual - 2147483648 ≤ -92682 := by omega
    nlinarith [mul_nonneg (show 0 ≤ 2147483648 - actual - 92682 by omega) (show (0 : ℤ) ≤ 2147483648 - actual + 92682 by omega)]
  have hi : actual ≤ 2147483648 + 92681 := by
    by_contra! h
    have hh : 92682 ≤ actual - 2147483648 := by omega
    nlinarith [mul_self_le_mul_self (by norm_num : (0 : ℤ) ≤ 92682) hh]
  obtain ⟨k, hk⟩ := divides
  simp only [orders, List.mem_cons, List.not_mem_nil, or_false, Prod.mk.injEq] at row
  rcases row with h | h | h | h | h | h | h | h <;> obtain ⟨rfl, rfl⟩ := h <;> omega

end M31HasseWitnesses
