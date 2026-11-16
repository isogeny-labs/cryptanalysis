import Std.Tactic
import Init.Grind.Ring.Basic

/-! Faithful universal implications for the actual degree13 rational maps.
The actual curve/morphism/degree, finite K-group and polarized product
interpretations remain separate written obligations. No custom axioms,
holes, native evaluation or assumed inverse conclusion. -/
set_option autoImplicit false
set_option maxRecDepth 10000
set_option maxHeartbeats 4000000
namespace OddSource223
open Lean.Grind

theorem cleared_rational_curve_map {K : Type} [CommRing K]
    (S T N D a b y d : K)
    (curve : S*T^2=N^3*D+a*N*D^3+b*D^4)
    (point : y^2=S) (unit : D*d=1) :
    (y*T*d^2)^2=(N*d)^3+a*(N*d)+b := by
  have h := congrArg (fun z : K => z*d^4) curve
  grind

theorem normalized_scaling_residual {K : Type} [CommRing K]
    (u x y a b : K) :
    (u^3*y)^2-(u^2*x)^3-(u^4*a)*(u^2*x)-u^6*b =
      u^6*(y^2-x^3-a*x-b) := by
  grind

theorem recovery_from_scalar_composition {A B : Type}
    (F : A → B) (G : B → A) (act : Nat → A → A)
    (plus : A → A → A) (zero : A) (n inv ell c : Nat)
    (mul : ∀ m k x, act (m*k) x=act m (act k x))
    (sum : ∀ m k x, act (m+k) x=plus (act m x) (act k x))
    (one : ∀ x, act 1 x=x) (zeroStable : ∀ m, act m zero=zero)
    (addZero : ∀ x, plus x zero=x)
    (torsion : ∀ x, act ell x=zero)
    (composition : ∀ x, G (F x)=act n x)
    (bezout : inv*n=1+c*ell) :
    ∀ x, act inv (G (F x))=x := by
  intro x
  rw [composition, ← mul, bezout, sum, mul, torsion, zeroStable, one, addZero]

theorem thirteen_odd_bezout :
    (639940 : Nat)*13=1+3*2773073 := by decide

theorem thirteen_full_rational_bezout :
    (3413013 : Nat)*13=1+4*11092292 := by decide

theorem proposed_fiftytwo_odd_bezout :
    (159985 : Nat)*52=1+3*2773073 := by decide

end OddSource223
