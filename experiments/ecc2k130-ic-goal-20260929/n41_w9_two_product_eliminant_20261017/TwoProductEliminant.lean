import Std
import Init.Grind.Ring.Basic

namespace TwoProductEliminant
open Lean.Grind

/-- The characteristic-two quadratic resultant vanishes at a common root.
    The coefficient expressions are the ones used in the Sage eliminant. -/
theorem quadratic_common_root {F : Type} [Field F]
    (C H q A B D b : F) (charTwo : ∀ x : F, x + x = 0)
    (first : C*b*b + q*b + H = 0)
    (second : A*b*b + B*b + D = 0) :
    let M := A*H + C*D
    let L := A*q + C*B
    let N := B*H + q*D
    M*M + L*N = 0 := by
  dsimp
  have hM : A*H + C*D = b*(A*q + C*B) := by
    have := charTwo (A*C*b*b)
    have := charTwo (A*q*b)
    have := charTwo (C*B*b)
    grind +ring
  have hN : B*H + q*D = b*b*(A*q + C*B) := by
    have := charTwo (B*q*b)
    have := charTwo (B*C*b*b)
    have := charTwo (q*A*b*b)
    grind +ring
  rw [hM, hN]
  have := charTwo (b*b*(A*q+C*B)*(A*q+C*B))
  grind +ring

/-- The norm of a linear remainder vanishes when it vanishes at a root
    of the source quadratic. -/
theorem linear_remainder_norm {F : Type} [Field F]
    (C p H a r0 r1 : F) (charTwo : ∀ x : F, x + x = 0)
    (source : C*a*a + p*a + H = 0)
    (remainder : r0 + r1*a = 0) :
    C*r0*r0 + p*r0*r1 + H*r1*r1 = 0 := by
  have hr : r0 = r1*a := by
    have := charTwo (r1*a)
    grind +ring
  rw [hr]
  grind +ring

/-- The two norm stages compose if polynomial division supplies the stated
    linear remainder identity at the first root. -/
theorem two_product_sound {F : Type} [Field F]
    (C1 H1 p C2 H2 q A B D a b r0 r1 : F)
    (charTwo : ∀ x : F, x + x = 0)
    (first : C1*a*a + p*a + H1 = 0)
    (second : C2*b*b + q*b + H2 = 0)
    (sumEquation : A*b*b + B*b + D = 0)
    (remainderIdentity :
      (A*H2+C2*D)*(A*H2+C2*D) +
      (A*q+C2*B)*(B*H2+q*D) = r0+r1*a) :
    C1*r0*r0 + p*r0*r1 + H1*r1*r1 = 0 := by
  have hzero := quadratic_common_root C2 H2 q A B D b charTwo second sumEquation
  have hr : r0+r1*a=0 := by rw [← remainderIdentity]; exact hzero
  exact linear_remainder_norm C1 p H1 a r0 r1 charTwo first hr

#print axioms quadratic_common_root
#print axioms linear_remainder_norm
#print axioms two_product_sound

end TwoProductEliminant
