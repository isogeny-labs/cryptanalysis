import Std

namespace FourCodeBox

/-- A zero quotient fingerprint excludes every fourth-state branch in each
specialized root of a complete four-axis code box. The exact evaluation of
the norm product is an explicit hypothesis checked for the N41 instance. -/
theorem zero_quotient_excludes_four_axis_box
    {α β γ δ υ κ φ : Type} [Zero κ] [Zero φ] [One φ] [DecidableEq φ]
    (h01 : (0 : φ) ≠ 1)
    (first : List α) (second : List β) (third : List γ) (fourth : List δ)
    (roots : α → β → List υ)
    (norm : α → β → γ → δ → υ → Fin 4 → φ)
    (evaluate : α → β → γ → δ → υ → κ → φ)
    (residue : κ)
    (hzero : residue = 0)
    (heval_zero : ∀ a b c d u, evaluate a b c d u 0 = 0)
    (heval_indicator : ∀ a b c d u,
      evaluate a b c d u residue =
        if (∃ branch : Fin 4, norm a b c d u branch = 0) then 1 else 0) :
    ∀ a ∈ first, ∀ b ∈ second, ∀ c ∈ third, ∀ d ∈ fourth,
      ∀ u ∈ roots a b, ∀ branch : Fin 4, norm a b c d u branch ≠ 0 := by
  intro a _ b _ c _ d _ u _ branch hnorm
  have hvalue : evaluate a b c d u residue = (0 : φ) := by
    rw [hzero]
    exact heval_zero a b c d u
  have hindicator := heval_indicator a b c d u
  have hit : ∃ other : Fin 4, norm a b c d u other = 0 := ⟨branch, hnorm⟩
  simp only [hit, ↓reduceIte] at hindicator
  exact h01 (hvalue.symm.trans hindicator)

#print axioms zero_quotient_excludes_four_axis_box

end FourCodeBox
