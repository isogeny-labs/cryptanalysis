import Std
import Init.Grind.Ring.Basic

/-! A tree of local sum conditions lifts coherently through sign ambiguity. -/
namespace TreeLift
open Lean.Grind

def Signed {G : Type} [AddCommGroup G] (x a : G) : Prop := x = a ∨ x = -a

def Link {G : Type} [AddCommGroup G] (a b c : G) : Prop :=
  ∃ x y : G, Signed x a ∧ Signed y b ∧ Signed (x + y) c

theorem signed_neg {G : Type} [AddCommGroup G] {x a : G}
    (h : Signed x a) : Signed (-x) a := by
  rcases h with h | h
  · right
    simpa [h]
  · left
    simpa [h, AddCommGroup.neg_neg]

/-- A local link can realize either chosen sign of its parent by flipping
    both children together. -/
theorem link_lift {G : Type} [AddCommGroup G] {a b c t : G}
    (h : Link a b c) (ht : Signed t c) :
    ∃ x y : G, Signed x a ∧ Signed y b ∧ x + y = t := by
  obtain ⟨x, y, hx, hy, hs⟩ := h
  rcases hs with hs | hs
  · rcases ht with ht | ht
    · exact ⟨x, y, hx, hy, hs.trans ht.symm⟩
    · refine ⟨-x, -y, signed_neg hx, signed_neg hy, ?_⟩
      calc
        -x + -y = -(x + y) := (AddCommGroup.neg_add x y).symm
        _ = -c := by rw [hs]
        _ = t := ht.symm
  · rcases ht with ht | ht
    · refine ⟨-x, -y, signed_neg hx, signed_neg hy, ?_⟩
      calc
        -x + -y = -(x + y) := (AddCommGroup.neg_add x y).symm
        _ = c := by rw [hs, AddCommGroup.neg_neg]
        _ = t := ht.symm
    · exact ⟨x, y, hx, hy, hs.trans ht.symm⟩

/-- Five locally liftable links in the balanced six-leaf tree admit one
    globally consistent signed group sum equal to the target. -/
theorem six_leaf_lift
    {G : Type} [AddCommGroup G]
    (p₀ p₁ p₂ p₃ p₄ p₅ s₀₁ s₂₃ s₄₅ s₀₁₂₃ target : G)
    (h₀₁ : Link p₀ p₁ s₀₁)
    (h₂₃ : Link p₂ p₃ s₂₃)
    (h₄₅ : Link p₄ p₅ s₄₅)
    (h₀₁₂₃ : Link s₀₁ s₂₃ s₀₁₂₃)
    (hfinal : Link s₀₁₂₃ s₄₅ target) :
    ∃ q₀ q₁ q₂ q₃ q₄ q₅ : G,
      Signed q₀ p₀ ∧ Signed q₁ p₁ ∧ Signed q₂ p₂ ∧
      Signed q₃ p₃ ∧ Signed q₄ p₄ ∧ Signed q₅ p₅ ∧
      (((((q₀ + q₁) + q₂) + q₃) + q₄) + q₅) = target := by
  obtain ⟨u, v, hu, hv, hroot⟩ := link_lift hfinal (Or.inl rfl)
  obtain ⟨a, b, ha, hb, hleft⟩ := link_lift h₀₁₂₃ hu
  obtain ⟨q₄, q₅, h₄, h₅, hright⟩ := link_lift h₄₅ hv
  obtain ⟨q₀, q₁, h₀, h₁, hfirst⟩ := link_lift h₀₁ ha
  obtain ⟨q₂, q₃, h₂, h₃, hsecond⟩ := link_lift h₂₃ hb
  refine ⟨q₀, q₁, q₂, q₃, q₄, q₅, h₀, h₁, h₂, h₃, h₄, h₅, ?_⟩
  calc
    (((((q₀ + q₁) + q₂) + q₃) + q₄) + q₅)
        = ((q₀ + q₁) + (q₂ + q₃)) + (q₄ + q₅) := by
          simp only [AddCommMonoid.add_assoc]
    _ = (a + b) + v := by rw [hfirst, hsecond, hright]
    _ = u + v := by rw [hleft]
    _ = target := hroot

#print axioms TreeLift.signed_neg
#print axioms TreeLift.link_lift
#print axioms TreeLift.six_leaf_lift

end TreeLift
