import Std.Tactic
import Init.Grind.Module.Basic
set_option autoImplicit false
namespace NondualComposition
open Lean.Grind

/-- Compose two genuine dual pairs. The scalar conclusions for each individual
pair and the two required linearity laws are hypotheses; the composite scalar
conclusion is derived. These are functions on modules, not constructed curves. -/
theorem both_composite_norms {A B C : Type}
    [IntModule A] [IntModule B] [IntModule C]
    (f : A → B) (fh : B → A) (g : B → C) (gh : C → B)
    (n m : Int)
    (hf : ∀ a, fh (f a) = n • a)
    (hfh : ∀ b, f (fh b) = n • b)
    (hg : ∀ b, gh (g b) = m • b)
    (hgh : ∀ c, g (gh c) = m • c)
    (hfl : ∀ k : Int, ∀ b, fh (k • b) = k • fh b)
    (hgl : ∀ k : Int, ∀ b, g (k • b) = k • g b) :
    (∀ a, fh (gh (g (f a))) = (n*m) • a) ∧
      (∀ c, g (f (fh (gh c))) = (n*m) • c) := by
  constructor
  · intro a
    rw [hg, hfl, hf, ← IntModule.mul_zsmul, Int.mul_comm]
  · intro c
    rw [hfh, hgl, hgh, ← IntModule.mul_zsmul]

/-- Specialization for the two actual degree13 elliptic pairs; it remains
conditional on their actual group/morphism interpretation. The cyclic-kernel
classification, finite field and polarized Jacobian models are not encoded. -/
theorem both_composite_169 {A B C : Type}
    [IntModule A] [IntModule B] [IntModule C]
    (f : A → B) (fh : B → A) (g : B → C) (gh : C → B)
    (hf : ∀ a, fh (f a) = (13 : Int) • a)
    (hfh : ∀ b, f (fh b) = (13 : Int) • b)
    (hg : ∀ b, gh (g b) = (13 : Int) • b)
    (hgh : ∀ c, g (gh c) = (13 : Int) • c)
    (hfl : ∀ k : Int, ∀ b, fh (k • b) = k • fh b)
    (hgl : ∀ k : Int, ∀ b, g (k • b) = k • g b) :
    (∀ a, fh (gh (g (f a))) = (169 : Int) • a) ∧
      (∀ c, g (f (fh (gh c))) = (169 : Int) • c) := by
  exact both_composite_norms f fh g gh 13 13 hf hfh hg hgh hfl hgl

end NondualComposition
#print axioms NondualComposition.both_composite_norms
#print axioms NondualComposition.both_composite_169
