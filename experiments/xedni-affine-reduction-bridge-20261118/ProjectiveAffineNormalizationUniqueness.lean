import ProjectiveGenericNormalization
import Mathlib.Tactic

/-! Integral projective representatives with `Z = 1` are unique in a
rational projective class. Their coefficientwise reductions are therefore
independent of the representative chosen within this affine slice. -/
namespace XedniProjectiveAffineNormalizationUniqueness

open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

variable {R : Type*} [CommRing R] [NoZeroDivisors R] [Nontrivial R]

/-- Two equivalent projective representatives with the same unit-normalized
`Z` coordinate are equal. -/
theorem affine_z_one_equiv_iff_eq (U V : Fin 3 → R)
    (hU : U 2 = 1) (hV : V 2 = 1) : U ≈ V ↔ U = V := by
  apply WeierstrassCurve.Projective.equiv_iff_eq_of_Z_eq
  · rw [hU, hV]
  · rw [hV]
    exact one_ne_zero

private def q : ℤ →+* ℚ := Int.castRingHom ℚ

/-- An integral affine `Z=1` representative of a rational projective class
is unique as an integer coordinate vector. -/
theorem integral_affine_representative_unique (U V : Fin 3 → ℤ)
    (hU : U 2 = 1) (hV : V 2 = 1)
    (hClass : mapClass q (⟦U⟧ : WeierstrassCurve.Projective.PointClass ℤ) =
      mapClass q ⟦V⟧) : U = V := by
  change (⟦q ∘ U⟧ : WeierstrassCurve.Projective.PointClass ℚ) = ⟦q ∘ V⟧ at hClass
  have hEqQ : q ∘ U = q ∘ V := by
    apply (affine_z_one_equiv_iff_eq (q ∘ U) (q ∘ V)
      (by simpa [q] using congrArg q hU)
      (by simpa [q] using congrArg q hV)).mp
    exact Quotient.eq.mp hClass
  ext i
  have hi : q (U i) = q (V i) := congrFun hEqQ i
  change ((U i : ℤ) : ℚ) = ((V i : ℤ) : ℚ) at hi
  exact_mod_cast hi

/-- Every ring reduction of the unique integral affine representative is
independent of its choice. -/
theorem integral_affine_reduction_independent {S : Type*} [CommRing S]
    (g : ℤ →+* S) (U V : Fin 3 → ℤ)
    (hU : U 2 = 1) (hV : V 2 = 1)
    (hClass : mapClass q (⟦U⟧ : WeierstrassCurve.Projective.PointClass ℤ) =
      mapClass q ⟦V⟧) :
    mapClass g (⟦U⟧ : WeierstrassCurve.Projective.PointClass ℤ) =
      mapClass g ⟦V⟧ := by
  rw [integral_affine_representative_unique U V hU hV hClass]

#print axioms affine_z_one_equiv_iff_eq
#print axioms integral_affine_representative_unique
#print axioms integral_affine_reduction_independent

end XedniProjectiveAffineNormalizationUniqueness
