import Std.Tactic
import Init.Grind.Module.Basic
set_option autoImplicit false
namespace NormPointReuse
open Lean.Grind

/-- A half and a rational two-torsion correction have the same doubled norm. -/
theorem corrected_lift_doubles {A : Type} [IntModule A]
    (p t q : A) (half : (2 : Int) • p = q)
    (correction_two_torsion : (2 : Int) • t = 0) :
    (2 : Int) • (p + t) = q := by
  rw [IntModule.zsmul_add, half, correction_two_torsion]
  grind

/-- The transported norm is derived from duality, linearity, a half and
2-torsion correction. Equality with the old transported norm is not assumed. -/
theorem corrected_norm_reuse {A B J : Type} [IntModule A] [IntModule B]
    (g : A → B) (phi : B → J) (norm : J → B)
    (duality : ∀ z, norm (phi z) = (2 : Int) • z)
    (linear_two : ∀ a, g ((2 : Int) • a) = (2 : Int) • g a)
    (p t q : A) (half : (2 : Int) • p = q)
    (correction_two_torsion : (2 : Int) • t = 0) :
    norm (phi (g (p + t))) = (2 : Int) • g (p + t) ∧
      (2 : Int) • g (p + t) = g q := by
  constructor
  · exact duality _
  · rw [← linear_two, corrected_lift_doubles p t q half correction_two_torsion]

/-- For a factored elliptic composition the reused final point has the same
transported norm as evaluating both original maps on the source norm. -/
theorem factored_norm_reuse {A B C J : Type}
    [IntModule A] [IntModule B] [IntModule C]
    (g : A → B) (h : B → C) (phi : C → J) (norm : J → C)
    (duality : ∀ z, norm (phi z) = (2 : Int) • z)
    (g_linear_two : ∀ a, g ((2 : Int) • a) = (2 : Int) • g a)
    (h_linear_two : ∀ b, h ((2 : Int) • b) = (2 : Int) • h b)
    (p t q : A) (half : (2 : Int) • p = q)
    (correction_two_torsion : (2 : Int) • t = 0) :
    norm (phi (h (g (p + t)))) = (2 : Int) • h (g (p + t)) ∧
      (2 : Int) • h (g (p + t)) = h (g q) := by
  apply corrected_norm_reuse (fun a => h (g a)) phi norm duality
  · intro a
    rw [g_linear_two, h_linear_two]
  · exact half
  · exact correction_two_torsion

end NormPointReuse
