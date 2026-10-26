import Mathlib.Algebra.Polynomial.Eval.Defs
import Mathlib.RingTheory.AdjoinRoot
import Mathlib.RingTheory.Ideal.Maps

namespace J1728QuarticConjugacy

variable {R : Type*} [CommRing R]

/-- Coefficient transport by an automorphism preserves every factor identity. -/
theorem conjugate_factor_identity (σ : R ≃+* R) (f g h : Polynomial R)
    (hfactor : f = g * h) :
    f.map σ.toRingHom = (g.map σ.toRingHom) * (h.map σ.toRingHom) := by
  rw [hfactor, Polynomial.map_mul]

/-- The transported ideal contains the image of every element it contained. -/
theorem conjugate_ideal_membership (σ : R ≃+* R) (I : Ideal R) (a : R)
    (ha : a ∈ I) : σ a ∈ I.map σ.toRingHom := by
  exact Ideal.mem_map_of_mem σ.toRingHom ha

/-- An exact coefficient conjugacy gives an isomorphism of quotient presentations. -/
noncomputable def conjugate_quotient_equiv (σ : R ≃+* R)
    (f g : Polynomial R) (h : f.map (σ : R →+* R) = g) :
    AdjoinRoot f ≃+* AdjoinRoot g :=
  AdjoinRoot.mapRingEquiv σ f g (by
    rw [h])

#print axioms conjugate_factor_identity
#print axioms conjugate_ideal_membership
#print axioms conjugate_quotient_equiv

end J1728QuarticConjugacy
