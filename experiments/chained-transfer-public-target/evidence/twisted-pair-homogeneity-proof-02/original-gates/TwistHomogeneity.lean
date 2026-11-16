import Std.Tactic
set_option autoImplicit false
namespace TwistHomogeneity
open Lean.Grind

/-! Polynomial identities only. These declarations do not construct elliptic
curves, a finite field, an HLP quotient, a square root in an encoded field, or a
Rust evaluator. The determinant/adjugate and cleared-numerator representations
must still be matched to the actual original constructor. -/

/-- The usual short-Weierstrass twist coordinate scaling over a ring containing
a chosen square root. Invertibility and geometric isomorphism are separate. -/
theorem short_twist_residual {R : Type} [CommRing R]
    (v s a b x y : R) (root : s^2 = v) :
    (v*s*y)^2 - ((v*x)^3 + (v^2*a)*(v*x) + v^3*b) =
      v^3 * (y^2 - (x^3 + a*x + b)) := by
  grind

theorem delta_scale {R : Type} [CommRing R] (v a b : R) :
    (v*a)^2 - 4*(v^2*b) = v^2*(a^2 - 4*b) := by
  grind

def det3 {R : Type} [CommRing R]
    (a b c d e f g h i : R) : R :=
  a*(e*i-f*h) - b*(d*i-f*g) + c*(d*h-e*g)

/-- Every entry of an adjugate is a signed2x2 minor. This states the
coordinate polynomial used for each such minor, without an encoded matrix. -/
theorem adjugate_minor_scale {R : Type} [CommRing R]
    (v a b c d : R) :
    (v*a)*(v*d) - (v*b)*(v*c) = v^2*(a*d-b*c) := by
  grind

theorem determinant_scale {R : Type} [CommRing R]
    (v a b c d e f g h i : R) :
    det3 (v*a) (v*b) (v*c) (v*d) (v*e) (v*f) (v*g) (v*h) (v*i) =
      v^3 * det3 a b c d e f g h i := by
  unfold det3
  grind

/-- Clear the three Delta denominators in the primary HLP twisting-factor
formula. Actual denominator nonzero/inverse and constructor equality remain
explicit bridges; this polynomial identity does not erase those conditions. -/
def twistingNumerator {R : Type} [CommRing R]
    (r a b c d e f : R) : R :=
  r*(a^2*e*f+b^2*d*f+c^2*d*e-d*e*f)-2*a*b*c*d*e*f

theorem twisting_numerator_scale {R : Type} [CommRing R]
    (v r a b c d e f : R) :
    twistingNumerator (v^3*r) (v*a) (v*b) (v*c) (v^2*d) (v^2*e) (v^2*f) =
      v^9 * twistingNumerator r a b c d e f := by
  unfold twistingNumerator
  grind

def ciani {R : Type} [CommRing R]
    (a b c d e f x y z : R) : R :=
  a*x^4+b*y^4+c*z^4+2*d*x^2*y^2+2*e*x^2*z^2+2*f*y^2*z^2

theorem ciani_coefficient_scale {R : Type} [CommRing R]
    (v a b c d e f x y z : R) :
    ciani (v^2*a) (v^2*b) (v^2*c) (v^2*d) (v^2*e) (v^2*f) x y z =
      v^2*ciani a b c d e f x y z := by
  unfold ciani
  grind

/-- The common coefficient scale preserves zeros if its factor has an inverse.
No field encoding or projective-curve isomorphism is asserted. -/
theorem invertible_square_scale_zero {R : Type} [CommRing R]
    (v w z : R) (inverse : v*w=1) :
    (v^2*z=0) ↔ z=0 := by
  constructor <;> intro h <;> grind

/-- Finite natural-number residue witnesses only. Their interpretation in the
actual F223/K presentation and HLP D values remains independently checked. -/
theorem fixed_pair_modular_witnesses :
    (15 : Nat)^2 % 223 = 2 ∧
    (144 : Nat)^2 % 223 = (12^3*12 : Nat) % 223 ∧
    (153 : Nat)^2 % 223 = (12^3*24 : Nat) % 223 ∧
    144 % 223 ≠ 0 ∧ 153 % 223 ≠ 0 := by
  decide

end TwistHomogeneity
