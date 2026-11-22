import Std
import Init.Grind.Ring.Basic

namespace TargetTowerSound
open Lean.Grind

def f3 {R : Type} [CommRing R] (a b z : R) : R :=
  (1+(a*b)^2)*z^2+a*b*z+(a^2+b^2)

def resultant {R : Type} [CommRing R] (A B C D E F : R) : R :=
  (A*F+C*D)^2+(A*E+B*D)*(B*F+C*E)

def f4 {R : Type} [CommRing R] (a b c z : R) : R :=
  resultant (1+(a*b)^2) (a*b) (a^2+b^2)
    (1+(c*z)^2) (c*z) (c^2+z^2)

/-- S3's two partial-output positions can be exchanged. -/
theorem f3_swap_middle {R : Type} [CommRing R] (a b c : R) :
    f3 a b c = f3 a c b := by
  unfold f3
  grind +ring

/-- The characteristic-two quadratic resultant vanishes when both input
    quadratics vanish at the same intermediate coordinate. -/
theorem common_quadratic_root {R : Type} [CommRing R]
    (A B C D E F m : R) (charTwo : ∀ x : R, x+x=0)
    (hfirst : A*m^2+B*m+C=0)
    (hsecond : D*m^2+E*m+F=0) :
    resultant A B C D E F=0 := by
  let U := A*F+C*D
  let V := A*E+B*D
  let W := B*F+C*E
  have hlinear : V*m+U=0 := by
    have := charTwo (A*D*m^2)
    grind +ring
  have hquadratic : V*m^2+W=0 := by
    have := charTwo (B*E*m)
    grind +ring
  change U^2+V*W=0
  have := charTwo (V^2*m^2)
  grind +ring

/-- The public target can be inserted before eliminating the two right
    pair-output roots. The two S3 links imply the target F4 constraint. -/
theorem right_target_f4_zero {R : Type} [CommRing R]
    (d e z t middle : R) (charTwo : ∀ x : R, x+x=0)
    (rightPair : f3 d e middle=0)
    (publicSum : f3 z middle t=0) :
    f4 d e z t=0 := by
  have hswapped : f3 z t middle=0 := by
    rw [f3_swap_middle z t middle]
    exact publicSum
  unfold f3 at rightPair hswapped
  unfold f4
  exact common_quadratic_root _ _ _ _ _ _ middle charTwo rightPair hswapped

def rightRootProduct {R : Type} [CommRing R]
    (d0 d1 e0 e1 z t : R) : R :=
  (f4 d0 e0 z t*f4 d1 e0 z t)*
  (f4 d0 e1 z t*f4 d1 e1 z t)

/-- Both quadratic norms vanish if one selected right-root pair satisfies
    the public-target F4 equation. -/
theorem right_root_product_zero {R : Type} [CommRing R]
    (d0 d1 e0 e1 z t middle : R)
    (charTwo : ∀ x : R, x+x=0)
    (rightPair : f3 d0 e0 middle=0)
    (publicSum : f3 z middle t=0) :
    rightRootProduct d0 d1 e0 e1 z t=0 := by
  have h := right_target_f4_zero d0 e0 z t middle charTwo rightPair publicSum
  simp [rightRootProduct, h]

#print axioms f3_swap_middle
#print axioms common_quadratic_root
#print axioms right_target_f4_zero
#print axioms right_root_product_zero

end TargetTowerSound
