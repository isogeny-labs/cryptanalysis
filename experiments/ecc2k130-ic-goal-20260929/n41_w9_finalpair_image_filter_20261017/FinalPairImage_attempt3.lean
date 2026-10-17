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
  rcases Field.of_mul_eq_zero hfactor with hp | hk
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

/-- A field element shared by the source and target quadratics makes the
final-pair resultant vanish, even before a sparse source code is imposed. -/
theorem shared_root_resultant_zero {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0)
    (A B D C H p e : F)
    (source : C*e*e+p*e+H=0)
    (target : A*e*e+B*e+D=0) :
    let M := A*H+C*D
    let L := A*p+C*B
    let N := B*H+p*D
    M*M+L*N=0 := by
  dsimp
  have hg : C*(A*e*e+B*e+D) =
      (A*p+C*B)*e+(A*H+C*D) := by
    grind +ring
  have hn : (A*p+C*B)*e*e+(B*H+p*D)=0 := by
    have hcross := charTwo (p*B*e)
    grind +ring
  have hm : (A*p+C*B)*e+(A*H+C*D)=0 := by
    rw [← hg, target]
    ring
  have hdouble := charTwo ((A*p+C*B)*(A*p+C*B)*e*e)
  grind +ring

/-- Every nonzero target-link root determines an unrestricted field
product satisfying the source quadratic. Source sparsity is the further
condition needed for a factor-base pair. -/
theorem unrestricted_product_from_root {F : Type} [Field F]
    (charTwo : ∀ x : F, x+x=0)
    (C H e : F) (he : e ≠ 0) :
    ∃ p : F, C*e*e+p*e+H=0 := by
  refine ⟨(C*e*e+H)*e⁻¹, ?_⟩
  have hunit : e⁻¹*e=1 := Field.inv_mul_cancel he
  have hinv : ((C*e*e+H)*e⁻¹)*e = C*e*e+H := by
    grind +ring
  have hcancel := charTwo (C*e*e+H)
  grind +ring

#print axioms FinalPairImage.map_additive
#print axioms FinalPairImage.equal_output_two_preimages
#print axioms FinalPairImage.second_root
#print axioms FinalPairImage.shared_root_resultant_zero
#print axioms FinalPairImage.unrestricted_product_from_root

end FinalPairImage
