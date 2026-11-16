import Std.Tactic
import Init.Grind.Module.Basic
set_option autoImplicit false
namespace ThreePairNorm
open Lean.Grind

/-- Three individual dual norms and the stated linearity laws imply both
composite norms. Actual curves, projective extensions and Jacobians are not
encoded by these abstract modules. No composite norm is assumed. -/
theorem three_pair_norms {A B C D : Type}
    [IntModule A] [IntModule B] [IntModule C] [IntModule D]
    (f : A → B) (fh : B → A) (g : B → C) (gh : C → B)
    (h : C → D) (hh : D → C) (n m k : Int)
    (hf : ∀ a, fh (f a) = n • a)
    (hfh : ∀ b, f (fh b) = n • b)
    (hg : ∀ b, gh (g b) = m • b)
    (hgh : ∀ c, g (gh c) = m • c)
    (hhf : ∀ c, hh (h c) = k • c)
    (hhb : ∀ d, h (hh d) = k • d)
    (hfl : ∀ z : Int, ∀ b, fh (z • b) = z • fh b)
    (hghl : ∀ z : Int, ∀ c, gh (z • c) = z • gh c)
    (hgl : ∀ z : Int, ∀ b, g (z • b) = z • g b)
    (hhl : ∀ z : Int, ∀ c, h (z • c) = z • h c) :
    (∀ a, fh (gh (hh (h (g (f a))))) = (n*m*k) • a) ∧
      (∀ d, h (g (f (fh (gh (hh d))))) = (n*m*k) • d) := by
  constructor
  · intro a
    rw [hhf, hghl, hg, hfl, hfl, hf,
      ← IntModule.mul_zsmul, ← IntModule.mul_zsmul]
    have scalars : k*m*n = n*m*k := by ac_rfl
    rw [scalars]
  · intro d
    rw [hfh, hgl, hgh, hhl, hhl, hhb,
      ← IntModule.mul_zsmul, ← IntModule.mul_zsmul]

/-- A dual scalar norm with an explicit Bezout witness recovers points on the
given annihilator subgroup, hence gives injectivity there. The map is arbitrary;
the needed norm and annihilator identities are explicit hypotheses. -/
theorem norm_injective_on_annihilator {A B : Type} [IntModule A]
    (f : A → B) (fh : B → A) (n p u v : Int)
    (norm : ∀ a, fh (f a) = n • a)
    (bezout : u*n+v*p=1)
    (a b : A) (ha : p • a=0) (hb : p • b=0) (same : f a=f b) :
    a=b := by
  have recover : ∀ x : A, p • x=0 → x=u • (n • x) := by
    intro x hx
    calc
      x = (u*n+v*p) • x := by rw [bezout, IntModule.one_zsmul]
      _ = u • (n • x) + v • (p • x) := by
        rw [IntModule.add_zsmul, IntModule.mul_zsmul, IntModule.mul_zsmul]
      _ = u • (n • x) := by
        rw [hx, IntModule.zsmul_zero]
        grind
  have equal_norms : n • a=n • b := by rw [← norm a, ← norm b, same]
  calc
    a = u • (n • a) := recover a ha
    _ = u • (n • b) := by rw [equal_norms]
    _ = b := (recover b hb).symm

/-- Fixed numeric coprimality checks only. Actual Jacobian norms, subgroup
annihilators and the field/geometric/program bridges are supplied separately. -/
theorem fixed_scalar_gcd :
    Nat.gcd 2197 2773073 = 1 ∧ Nat.gcd 13 2771711 = 1 := by
  decide

end ThreePairNorm
