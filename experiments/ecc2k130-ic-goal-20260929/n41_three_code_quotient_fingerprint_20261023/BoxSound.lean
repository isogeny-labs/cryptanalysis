import Std

namespace ThreeCodeBox

/-- A zero quotient element excludes every exact zero of the norm in a
three-axis code box, provided specialization is a zero-preserving evaluation
and the fingerprint specializes to the zero-test indicator. -/
theorem zero_quotient_excludes_box
    {α β γ υ κ φ : Type} [Zero κ] [Zero φ] [One φ] [DecidableEq φ]
    (h01 : (0 : φ) ≠ 1)
    (left : List α) (middle : List β) (right : List γ)
    (roots : α → β → List υ)
    (norm : α → β → γ → υ → φ)
    (evaluate : α → β → γ → υ → κ → φ)
    (residue : κ)
    (hzero : residue = 0)
    (heval_zero : ∀ a b c u, evaluate a b c u 0 = 0)
    (heval_indicator : ∀ a b c u,
      evaluate a b c u residue = if norm a b c u = 0 then 1 else 0) :
    ∀ a ∈ left, ∀ b ∈ middle, ∀ c ∈ right, ∀ u ∈ roots a b,
      norm a b c u ≠ 0 := by
  intro a _ b _ c _ u _ hnorm
  have hvalue : evaluate a b c u residue = (0 : φ) := by
    rw [hzero]
    exact heval_zero a b c u
  have hindicator := heval_indicator a b c u
  rw [hnorm] at hindicator
  simp only at hindicator
  exact h01 (hvalue.symm.trans hindicator)

#print axioms zero_quotient_excludes_box

end ThreeCodeBox
