import Std
import Init.Grind.Ring.Basic

namespace FinalPairImage
open Lean.Grind

/-- A binary-linearized quadratic is additive in its source product. -/
theorem map_additive {R : Type} [CommRing R]
    (charTwo : ∀ x : R, x+x=0) (a b p q : R) :
    a*(p+q)*(p+q)+b*(p+q) =
      (a*p*p+b*p)+(a*q*q+b*q) := by
  have hcross := charTwo (a*p*q)
  grind +ring

/-- Two products with the same output are equal or differ by the unique
nonzero element in the kernel of the field-wide map. -/
theorem equal_output_two_preimages {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0) (a b p q : F)
    (h : a*p*p+b*p = a*q*q+b*q) :
    p=q ∨ a*(p+q)+b=0 := by
  have hsum : (a*p*p+b*p)+(a*q*q+b*q)=0 := by
    rw [h]
    exact charTwo _
  have hcross := charTwo (a*p*q)
  have hfactor : (p+q)*(a*(p+q)+b)=0 := by
    grind +ring
  rcases mul_eq_zero.mp hfactor with hp | hk
  · left
    have hq := charTwo q
    grind
  · exact Or.inr hk

/-- Once one product root is known, adding the kernel step gives the
other root. This is the algebra used by the direct code-recovery filter. -/
theorem second_root {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0) (a b p step target : F)
    (hstep : a*step=b) (hroot : a*p*p+b*p=target) :
    a*(p+step)*(p+step)+b*(p+step)=target := by
  have hcancel := charTwo (a*p*step)
  have hkernel : a*step*step+b*step=0 := by
    have hbs := charTwo (b*step)
    grind +ring
  grind +ring

#print axioms FinalPairImage.map_additive
#print axioms FinalPairImage.equal_output_two_preimages
#print axioms FinalPairImage.second_root

end FinalPairImage
