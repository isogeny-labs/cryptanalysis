import ProjectivePrimitiveReductionMap
import Mathlib.Tactic

/-! Primitive integral coordinates preserve the homogeneous Weierstrass
equation when passing from rational classes to arbitrary coefficient rings. -/
namespace XedniProjectivePrimitiveCurveEquation

open XedniProjectivePrimitiveReductionMap
open WeierstrassCurve.Projective

private def q : ℤ →+* ℚ := Int.castRingHom ℚ

/-- The homogeneous curve equation, stated on a nonzero projective class.
Unit scaling leaves this proposition unchanged. -/
def OnCurve {R : Type*} [CommRing R] (W : WeierstrassCurve.Projective R)
    (C : NonzeroClass R) : Prop :=
  Quotient.liftOn C.val W.Equation
    (fun _ _ h => propext (W.equation_of_equiv h))

/-- A rational curve class has a primitive representative on the integral
curve, provided the curve coefficients are integral. -/
theorem representative_equation (W : WeierstrassCurve.Projective ℤ)
    (C : NonzeroClass ℚ)
    (hC : (W.map q).Equation (Quotient.out C.val)) :
    W.Equation (representative C) := by
  have hClass := XedniProjectivePrimitiveReductionMap.representative_class C
  change (⟦q ∘ representative C⟧ : PointClass ℚ) = C.val at hClass
  have hEquiv : (q ∘ representative C) ≈ Quotient.out C.val := by
    apply Quotient.eq.mp
    calc
      (⟦q ∘ representative C⟧ : PointClass ℚ) = C.val := hClass
      _ = ⟦Quotient.out C.val⟧ := (Quotient.out_eq C.val).symm
  have hRational : (W.map q).Equation (q ∘ representative C) :=
    ((W.map q).equation_of_equiv hEquiv).mpr hC
  exact (W.map_equation (show Function.Injective q from Int.cast_injective)
    (representative C)).mp hRational

/-- The chosen representative satisfies the equation after coefficient and
coordinate reduction through any ring homomorphism. -/
theorem reduced_representative_equation {S : Type*} [CommRing S]
    (W : WeierstrassCurve.Projective ℤ) (g : ℤ →+* S) (C : NonzeroClass ℚ)
    (hC : (W.map q).Equation (Quotient.out C.val)) :
    (W.map g).Equation (g ∘ representative C) :=
  (representative_equation W C hC).map g

/-- Primitive reduction carries a rational projective curve class to a
projective class on the reduced curve. -/
theorem reduceNonzero_onCurve {S : Type*} [CommRing S] [Nontrivial S]
    (W : WeierstrassCurve.Projective ℤ) (g : ℤ →+* S)
    (C : NonzeroClass ℚ) (hC : OnCurve (W.map q) C) :
    OnCurve (W.map g) (reduceNonzero g C) := by
  have hOut : (W.map q).Equation (Quotient.out C.val) := by
    have heq : (⟦Quotient.out C.val⟧ : PointClass ℚ) = C.val :=
      Quotient.out_eq C.val
    unfold OnCurve at hC
    rw [← heq] at hC
    exact hC
  change (W.map g).Equation (g ∘ representative C)
  exact reduced_representative_equation W g C hOut

#print axioms representative_equation
#print axioms reduced_representative_equation
#print axioms reduceNonzero_onCurve

end XedniProjectivePrimitiveCurveEquation
