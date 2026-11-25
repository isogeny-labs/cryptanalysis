import Mathlib.Tactic

namespace M31SignedSquare

abbrev base : Int := 2147483648
abbrev p : Int := 2147483647
def fold (v : Int) := v^2 / base + (v^2 % base - p)
def canonical (v : Int) := if v < 0 then v+p else v

theorem square_bound (v : Int) (lo : -p ≤ v) (hi : v ≤ p) :
    0 ≤ v^2 ∧ v^2 ≤ p^2 := by
  constructor
  · positivity
  · nlinarith [mul_nonneg (sub_nonneg.mpr hi) (by omega : 0 ≤ p + v)]

theorem no_saturation (v : Int) (lo : -p ≤ v) (hi : v ≤ p) :
    2*v^2 < 2^63 := by have := (square_bound v lo hi).2; norm_num [p] at *; omega

theorem fold_range (v : Int) (lo : -p ≤ v) (hi : v ≤ p) :
    -p ≤ fold v ∧ fold v < p := by
  obtain ⟨a,b⟩ := square_bound v lo hi
  unfold fold base p at *
  omega

theorem fold_equiv (v : Int) : fold v ≡ v^2 [ZMOD p] := by
  unfold fold Int.ModEq base p
  omega

theorem canonical_eq (v : Int) (lo : -p ≤ v) (hi : v < p) :
    canonical v = v % p := by unfold canonical p at *; split <;> omega

/-- Track both signs; squaring removes the sign from the previous representative. -/
theorem chain_equiv (negated : Bool) (x : Int) (n : Nat) :
    let update := fun v => if negated then -(fold v) else fold v
    let result := update^[n+1] x
    (if negated then -result else result) ≡ x^(2^(n+1)) [ZMOD p] := by
  dsimp only
  induction n with
  | zero =>
    cases negated <;> simpa using fold_equiv x
  | succ n ih =>
    rw [Function.iterate_succ_apply', pow_succ 2 (n+1), pow_mul]
    cases negated <;> simp only [Bool.false_eq_true, ite_false, ite_true, neg_neg] at *
    · exact (fold_equiv _).trans (ih.pow 2)
    · apply (fold_equiv _).trans
      simpa using ih.pow 2

end M31SignedSquare
