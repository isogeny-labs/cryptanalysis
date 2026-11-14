import Init.Grind.Ring.Basic
import Init.Grind.Module.Basic

/-! Conditional algebra for the written origin/reference bridge. Actual
divisors, Picard groups, the infinity involution and the concrete signed
source isomorphism are not defined here; their geometric identification is
an explicit written/native obligation. No custom axiom is introduced. -/
set_option autoImplicit false
namespace PublicOriginConvention
open Lean.Grind

theorem degree_six_reference_has_two_deltas
    {D : Type} [IntModule D] (canonical oldP newP divisor : D) :
    (divisor-(canonical-newP)-(canonical-newP))-
      (divisor-(canonical-oldP)-(canonical-oldP)) =
      (newP-oldP)+(newP-oldP) := by
  grind

theorem infinity_involution_origin_difference
    {E : Type} [IntModule E] (infinityMinus image : E) :
    (infinityMinus-image)-infinityMinus= -image := by
  grind

theorem transported_forward_double
    {E F J : Type} [IntModule E] [IntModule F] [IntModule J]
    (source : E → F) (inverse : F → E)
    (pullOld : E → J) (pullNew : F → J) (normNew : J → F)
    (map_bridge : ∀ x, pullOld x=pullNew (source x))
    (new_diagonal : ∀ y, normNew (pullNew y)=(2 : Int) • y)
    (inverse_two : ∀ y, inverse ((2 : Int) • y)=(2 : Int) • inverse y)
    (left_inverse : ∀ x, inverse (source x)=x) (x : E) :
    inverse (normNew (pullOld x))=(2 : Int) • x := by
  rw [map_bridge, new_diagonal, inverse_two, left_inverse]

theorem transported_reverse_double
    {E F J : Type} [IntModule E] [IntModule F] [IntModule J]
    (source : E → F) (inverse : F → E)
    (pullOld : E → J) (pullNew : F → J) (normNew : J → F)
    (map_bridge : ∀ x, pullOld x=pullNew (source x))
    (new_reverse : ∀ j, pullNew (normNew j)=(2 : Int) • j)
    (right_inverse : ∀ y, source (inverse y)=y) (j : J) :
    pullOld (inverse (normNew j))=(2 : Int) • j := by
  rw [map_bridge, right_inverse, new_reverse]

theorem common_sign_preserves_affine_log_ratio
    {K : Type} [CommRing K] (a b d k inverse : K)
    (denominator_unit : d*inverse=1) :
    (((-a)+k*(-d)+b)-((-a)+b))*(-inverse)=k := by
  grind

end PublicOriginConvention
