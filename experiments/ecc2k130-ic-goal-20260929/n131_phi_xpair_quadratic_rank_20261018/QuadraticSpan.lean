import Std

/-! A full-rank sample of quadratic Boolean feature rows eliminates every
XOR-linear annihilator of those rows. Concrete Q1358 rows and the rank
certificate are reconstructed by the independent Sage audit. -/
namespace QuadraticSpan

theorem feature_dimension : 1 + 131 + 131 * 130 / 2 = 8647 := by
  decide

inductive XorSpan (rows : List Nat) : Nat → Prop
  | zero : XorSpan rows 0
  | step (v row : Nat) : XorSpan rows v → row ∈ rows →
      XorSpan rows (Nat.xor v row)

theorem annihilator_zero_on_span (rows : List Nat) (L : Nat → Nat)
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

theorem full_quadratic_rank_excludes_annihilator (rows : List Nat) (L : Nat → Nat)
    (hlinear : ∀ a b, L (Nat.xor a b) = Nat.xor (L a) (L b))
    (hzero : L 0 = 0)
    (hrows : ∀ row ∈ rows, L row = 0)
    (hfull : ∀ v, v < 2 ^ 8647 → XorSpan rows v) :
    ∀ v, v < 2 ^ 8647 → L v = 0 := by
  intro v hv
  exact annihilator_zero_on_span rows L hlinear hzero hrows v (hfull v hv)

#print axioms feature_dimension
#print axioms annihilator_zero_on_span
#print axioms full_quadratic_rank_excludes_annihilator

end QuadraticSpan
