import Std

namespace TwoCodeTraceRank

theorem feature_count : 42 * (1 + 16 + 16 * 15 / 2) = 5754 := by
  decide

/-- Numeric source-code ordering forces the observed top-bit monomial to
vanish, independently of any curve output. -/
theorem ordered_top_bit_gate (a b : Nat)
    (_hb : b < 256) (hab : a < b) :
    (decide (128 ≤ a) && !(decide (128 ≤ b))) = false := by
  have himp : 128 ≤ a → 128 ≤ b := by omega
  by_cases ha : 128 ≤ a
  · have hb : 128 ≤ b := himp ha
    simp [ha, hb]
  · simp [ha]

inductive XorSpan (rows : List Nat) : Nat → Prop
  | zero : XorSpan rows 0
  | step (v row : Nat) : XorSpan rows v → row ∈ rows →
      XorSpan rows (Nat.xor v row)

theorem zero_on_span (rows : List Nat) (L : Nat → Nat)
    (hlinear : ∀ a b, L (Nat.xor a b) = Nat.xor (L a) (L b))
    (hzero : L 0 = 0)
    (hrows : ∀ row ∈ rows, L row = 0) :
    ∀ v, XorSpan rows v → L v = 0 := by
  intro v hv
  induction hv with
  | zero => exact hzero
  | step v row _ hrow ih =>
      rw [hlinear, ih, hrows row hrow]
      simp

/-- Full binary feature rank excludes a nonzero universal affine trace
predicate of the declared code degree and field-coordinate form. -/
theorem full_rank_sample_excludes_filter (rows : List Nat) (L : Nat → Nat)
    (hlinear : ∀ a b, L (Nat.xor a b) = Nat.xor (L a) (L b))
    (hzero : L 0 = 0)
    (hrows : ∀ row ∈ rows, L row = 0)
    (hfull : ∀ v, v < 2 ^ 5754 → XorSpan rows v) :
    ∀ v, v < 2 ^ 5754 → L v = 0 := by
  intro v hv
  exact zero_on_span rows L hlinear hzero hrows v (hfull v hv)

#print axioms feature_count
#print axioms ordered_top_bit_gate
#print axioms zero_on_span
#print axioms full_rank_sample_excludes_filter

end TwoCodeTraceRank
