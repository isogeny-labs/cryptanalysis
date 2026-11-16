import FiniteKernelPacking
import Mathlib.NumberTheory.Height.EllipticCurve
import Mathlib.NumberTheory.Height.NumberField

/-!
Under Northcott's property, the finite torsion subgroup of an elliptic curve
supplies the finite kernel set in the packing theorem. The projection into a
real normed space and its canonical-height properties remain explicit inputs.
-/

open Height Module

namespace XedniEllipticTorsionKernel

noncomputable section

variable {F : Type*} [Field F] [AdmissibleAbsValues F]
  [Northcott (logHeight₁ (K := F))] [DecidableEq F]
  (W : WeierstrassCurve.Affine F) [W.IsElliptic]

/-- The finite set of rational torsion points, obtained from Mathlib's
elliptic-curve Northcott and finite-torsion theorem. -/
def torsionKernel : Finset W.Point := by
  letI : Finite (AddCommGroup.torsion W.Point) :=
    WeierstrassCurve.Affine.finite_torsion
  letI : Fintype (AddCommGroup.torsion W.Point) := Fintype.ofFinite _
  classical
  exact Finset.univ.image (fun p : AddCommGroup.torsion W.Point => (p : W.Point))

theorem mem_torsionKernel {p : W.Point}
    (hp : p ∈ AddCommGroup.torsion W.Point) : p ∈ torsionKernel W := by
  letI : Finite (AddCommGroup.torsion W.Point) :=
    WeierstrassCurve.Affine.finite_torsion
  letI : Fintype (AddCommGroup.torsion W.Point) := Fintype.ofFinite _
  classical
  unfold torsionKernel
  exact Finset.mem_image.mpr ⟨⟨p, hp⟩, Finset.mem_univ _, rfl⟩

theorem torsionKernel_card :
    (torsionKernel W).card = Nat.card (AddCommGroup.torsion W.Point) := by
  letI : Finite (AddCommGroup.torsion W.Point) :=
    WeierstrassCurve.Affine.finite_torsion
  letI : Fintype (AddCommGroup.torsion W.Point) := Fintype.ofFinite _
  classical
  unfold torsionKernel
  rw [Finset.card_image_of_injective _ Subtype.coe_injective]
  simp only [Finset.card_univ, Nat.card_eq_fintype_card]

variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
  [FiniteDimensional ℝ E]

/-- The finite-kernel norm-gap theorem with the kernel instantiated as the
elliptic curve's torsion subgroup. -/
theorem bounded_relation_of_elliptic_torsion_norm_gap
    {r : ℕ} (points : Fin r → W.Point) (K : ℕ)
    (project : W.Point →+ E) (B δ : ℝ)
    (hB : 0 ≤ B) (hδ : 0 < δ)
    (hker : ∀ p : W.Point, project p = 0 →
      p ∈ AddCommGroup.torsion W.Point)
    (hpoint : ∀ i, ‖project (points i)‖ ≤ B)
    (hmin : ∀ p : W.Point, project p ≠ 0 → δ ≤ ‖project p‖)
    (hsmall : ((torsionKernel W).card : ℝ) *
      (1 + 2 * ((r : ℝ) * (K : ℝ) * B) / δ) ^ finrank ℝ E <
        ((2 * K + 1) ^ r : ℝ)) :
    ∃ coeff, XedniHeightPigeonhole.Nontrivial coeff ∧
      XedniHeightPigeonhole.Bounded (2 * K) coeff ∧
      XedniHeightPigeonhole.Relation points coeff := by
  exact XedniFiniteKernelPacking.bounded_relation_of_finite_kernel_norm_gap
    points K (torsionKernel W) project B δ hB hδ
    (fun p hp => mem_torsionKernel W (hker p hp)) hpoint hmin hsmall

/-- The rational-curve specialization uses Mathlib's number-field
Northcott instance to discharge torsion finiteness. -/
theorem bounded_relation_of_rational_curve_norm_gap
    (Wq : WeierstrassCurve.Affine ℚ) [Wq.IsElliptic]
    {Eq : Type*} [NormedAddCommGroup Eq] [NormedSpace ℝ Eq]
    [FiniteDimensional ℝ Eq]
    {r : ℕ} (points : Fin r → Wq.Point) (K : ℕ)
    (project : Wq.Point →+ Eq) (B δ : ℝ)
    (hB : 0 ≤ B) (hδ : 0 < δ)
    (hker : ∀ p : Wq.Point, project p = 0 →
      p ∈ AddCommGroup.torsion Wq.Point)
    (hpoint : ∀ i, ‖project (points i)‖ ≤ B)
    (hmin : ∀ p : Wq.Point, project p ≠ 0 → δ ≤ ‖project p‖)
    (hsmall : ((torsionKernel Wq).card : ℝ) *
      (1 + 2 * ((r : ℝ) * (K : ℝ) * B) / δ) ^ finrank ℝ Eq <
        ((2 * K + 1) ^ r : ℝ)) :
    ∃ coeff, XedniHeightPigeonhole.Nontrivial coeff ∧
      XedniHeightPigeonhole.Bounded (2 * K) coeff ∧
      XedniHeightPigeonhole.Relation points coeff := by
  exact bounded_relation_of_elliptic_torsion_norm_gap Wq points K
    project B δ hB hδ hker hpoint hmin hsmall

end

end XedniEllipticTorsionKernel

#print axioms XedniEllipticTorsionKernel.mem_torsionKernel
#print axioms XedniEllipticTorsionKernel.torsionKernel_card
#print axioms XedniEllipticTorsionKernel.bounded_relation_of_elliptic_torsion_norm_gap
#print axioms XedniEllipticTorsionKernel.bounded_relation_of_rational_curve_norm_gap
