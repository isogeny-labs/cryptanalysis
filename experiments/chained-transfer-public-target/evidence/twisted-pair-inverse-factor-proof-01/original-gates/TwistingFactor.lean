import Std.Tactic
set_option autoImplicit false
namespace TwistingFactor
open Lean.Grind

/-! The primary HLP rational expression represented by explicit inverse
witnesses. No inverse of a zero denominator is introduced implicitly. Actual
finite-field encoding, constructor inputs and geometry remain separate. -/
def factor {R : Type} [CommRing R]
    (r a b c inverseD0 inverseD1 inverseD2 : R) : R :=
  r*(a^2*inverseD0+b^2*inverseD1+c^2*inverseD2-1)-2*a*b*c

theorem scaled_delta_inverse {R : Type} [CommRing R]
    (v w delta inverseDelta : R)
    (inverseScale : v*w=1) (inverseDenominator : delta*inverseDelta=1) :
    (v^2*delta)*(w^2*inverseDelta)=1 := by
  grind

/-- Full HLP twisting-factor homogeneity when the new inverse denominators
are the old inverse denominators multiplied by the inverse scale squared. -/
theorem factor_scale {R : Type} [CommRing R]
    (v w r a b c inverseD0 inverseD1 inverseD2 : R)
    (inverseScale : v*w=1) :
    factor (v^3*r) (v*a) (v*b) (v*c)
      (w^2*inverseD0) (w^2*inverseD1) (w^2*inverseD2) =
      v^3 * factor r a b c inverseD0 inverseD1 inverseD2 := by
  unfold factor
  grind

/-- Match the primary HLP expression to the determinant polynomial of the
actual symmetric H matrix under its three explicit pair-product inverses. -/
theorem factor_equals_symmetric_determinant {R : Type} [CommRing R]
    (h0 h1 h2 a b c inverseD0 inverseD1 inverseD2 : R)
    (inverse0 : (h1*h2)*inverseD0=1)
    (inverse1 : (h0*h2)*inverseD1=1)
    (inverse2 : (h0*h1)*inverseD2=1) :
    factor (-(h0*h1*h2)) a b c inverseD0 inverseD1 inverseD2 =
      h0*h1*h2-h0*a^2-h1*b^2-h2*c^2-2*a*b*c := by
  unfold factor
  grind

end TwistingFactor
