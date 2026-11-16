import Std.Tactic
import Init.Grind.Ring.Basic

/-! Faithful universal identities for the actual classical HLP model panel.
Actual geometry, Galois descent, Picard maps and endpoint distinction are
separate obligations. No holes, custom axioms or native evaluation. -/
set_option autoImplicit false
set_option maxRecDepth 10000
set_option maxHeartbeats 4000000
namespace GluingModels223
open Lean.Grind

theorem translated_source_cubic {K : Type} [CommRing K] (a b r u : K) :
    (u+r)^3+a*(u+r)+b - (u^3+3*r*u^2+(3*r^2+a)*u) = r^3+a*r+b := by
  grind

theorem adjugate_diagonal_from_Delta {K : Type} [CommRing K]
    (h2 h3 A B : K) (delta : h2*h3=A^2-4*B) :
    h2*h3-A^2 = -4*B := by grind

theorem symmetric_adjugate_determinant {K : Type} [CommRing K]
    (h1 h2 h3 A1 A2 A3 : K) :
    let p := h2*h3-A1^2
    let q := h1*h3-A2^2
    let r := h1*h2-A3^2
    let u := A1*A2+h3*A3
    let v := A1*A3+h2*A2
    let w := A2*A3+h1*A1
    p*q*r+2*u*v*w-p*w^2-q*v^2-r*u^2 =
      (h1*h2*h3-h1*A1^2-h2*A2^2-h3*A3^2-2*A1*A2*A3)^2 := by
  dsimp
  grind

theorem symmetric_adjugate_cofactor {K : Type} [CommRing K]
    (h1 h2 h3 A1 A2 A3 : K) :
    (A1*A2+h3*A3)*(A1*A3+h2*A2)-(h2*h3-A1^2)*(A2*A3+h1*A1) =
      -A1*(h1*h2*h3-h1*A1^2-h2*A2^2-h3*A3^2-2*A1*A2*A3) := by
  grind

theorem symmetric_adjugate_pair_discriminant {K : Type} [CommRing K]
    (h1 h2 h3 A1 A2 A3 : K) :
    4*(A1*A2+h3*A3)^2-4*(h2*h3-A1^2)*(h1*h3-A2^2) =
      -4*h3*(h1*h2*h3-h1*A1^2-h2*A2^2-h3*A3^2-2*A1*A2*A3) := by
  grind

theorem even_quartic_discriminant {K : Type} [CommRing K]
    (a b c d e f : K) :
    (2*d*f-4*a*e)^2-4*(d^2-4*a*b)*(f^2-4*a*c) =
      -16*a*(4*a*b*c+d*e*f-a*e^2-b*f^2-c*d^2) := by
  grind

theorem even_quartic_map_residual {K : Type} [CommRing K]
    (alpha beta gamma s t v : K) (square : s^2=alpha) :
    let x := 2*s*v+2*alpha*t^2+beta
    let y := 2*s*x*t
    y^2-x*(x^2-2*beta*x+beta^2-4*alpha*gamma) =
      -4*alpha*x*(v^2-alpha*t^4-beta*t^2-gamma) := by
  dsimp
  rw [← square]
  grind

theorem even_quartic_map_on_jacobian {K : Type} [CommRing K]
    (alpha beta gamma s t v : K) (square : s^2=alpha)
    (point : v^2=alpha*t^4+beta*t^2+gamma) :
    let x := 2*s*v+2*alpha*t^2+beta
    let y := 2*s*x*t
    y^2=x*(x^2-2*beta*x+beta^2-4*alpha*gamma) := by
  have h := even_quartic_map_residual alpha beta gamma s t v square
  dsimp at h ⊢
  rw [point] at h
  grind

end GluingModels223
