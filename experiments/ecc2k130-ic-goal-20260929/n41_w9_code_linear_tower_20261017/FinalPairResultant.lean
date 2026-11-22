import Std
import Init.Grind.Ring.Basic

namespace FinalPairResultant
open Lean.Grind

/-- Expanding the quadratic resultant makes its dependence on the final
source product an additive quadratic in characteristic two. -/
theorem resultant_linearized {R : Type} [CommRing R]
    (A B D C H p : R) :
    let M := A*H+C*D
    let L := A*p+C*B
    let N := B*H+p*D
    M*M+L*N = (A*D)*p*p+(A*B*H+C*B*D)*p+
      (A*H+C*D)*(A*H+C*D)+C*B*B*H := by
  grind +ring

/-- The nonconstant part is additive in the product and hence binary-linear
in its source-code bits. -/
theorem code_map_additive {R : Type} [CommRing R]
    (charTwo : ∀ x : R, x+x=0) (K L p q : R) :
    K*(p+q)*(p+q)+L*(p+q) =
      (K*p*p+L*p)+(K*q*q+L*q) := by
  have := charTwo (K*p*q)
  grind +ring

/-- The resultant equals the product of the target quadratic at the two
known source roots, up to the nonzero square of the pair's leading term. -/
theorem resultant_split_identity {F : Type} [Field F]
    (charTwo : (2 : F)=0)
    (A B D C H p e0 e1 : F) (hC : C ≠ 0)
    (source0 : C*e0*e0+p*e0+H=0)
    (source1 : C*e1*e1+p*e1+H=0)
    (root_sum : C*(e0+e1)=p)
    (root_product : C*e0*e1=H) :
    let M := A*H+C*D
    let L := A*p+C*B
    let N := B*H+p*D
    M*M+L*N = C*C*(A*e0*e0+B*e0+D)*(A*e1*e1+B*e1+D) := by
  have h0 : C*(A*e0*e0+B*e0+D) = (A*p+C*B)*e0+(A*H+C*D) := by
    grind +ring
  have h1 : C*(A*e1*e1+B*e1+D) = (A*p+C*B)*e1+(A*H+C*D) := by
    grind +ring
  have h : C*((A*H+C*D)*(A*H+C*D)+
      (A*p+C*B)*(B*H+p*D)) =
      C*(C*(A*e0*e0+B*e0+D))*(C*(A*e1*e1+B*e1+D)) := by
    rw [h0,h1]
    grind +ring
  have hcancel : C ≠ 0 := hC
  grind +ring

/-- For a split, source-valid pair, a zero resultant is an exact root
condition, including the exceptional charts of the divided formula. -/
theorem resultant_zero_iff_source_root {F : Type} [Field F]
    (charTwo : (2 : F)=0)
    (A B D C H p e0 e1 : F) (hC : C ≠ 0)
    (source0 : C*e0*e0+p*e0+H=0)
    (source1 : C*e1*e1+p*e1+H=0)
    (root_sum : C*(e0+e1)=p)
    (root_product : C*e0*e1=H) :
    let M := A*H+C*D
    let L := A*p+C*B
    let N := B*H+p*D
    M*M+L*N=0 ↔
      (A*e0*e0+B*e0+D=0 ∨ A*e1*e1+B*e1+D=0) := by
  have h := resultant_split_identity charTwo A B D C H p e0 e1 hC
    source0 source1 root_sum root_product
  dsimp at h ⊢
  rw [h]
  constructor
  · intro hz
    rcases Field.of_mul_eq_zero hz with hleft | hright
    · rcases Field.of_mul_eq_zero hleft with hcc | h0
      · rcases Field.of_mul_eq_zero hcc with hc | hc
        · exact False.elim (hC hc)
        · exact False.elim (hC hc)
      · exact Or.inl h0
    · exact Or.inr hright
  · intro hroot
    rcases hroot with h0 | h1
    · rw [h0]; grind +ring
    · rw [h1]; grind +ring

#print axioms FinalPairResultant.resultant_linearized
#print axioms FinalPairResultant.code_map_additive
#print axioms FinalPairResultant.resultant_split_identity
#print axioms FinalPairResultant.resultant_zero_iff_source_root

end FinalPairResultant
