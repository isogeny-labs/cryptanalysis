import Mathlib.Algebra.Polynomial.Eval.Defs
import Mathlib.LinearAlgebra.Dimension.Finrank
import Mathlib.RingTheory.AdjoinRoot
import Mathlib.RingTheory.Ideal.Maps
import Mathlib.RingTheory.Ideal.Quotient.Operations

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

/-- If the coefficient automorphism fixes the base, the quotient equivalence
    preserves the base algebra structure. -/
noncomputable def conjugate_quotient_algEquiv
    {B L : Type*} [CommRing B] [CommRing L] [Algebra B L]
    (σ : L ≃ₐ[B] L) (f g : Polynomial L)
    (h : f.map (σ : L →+* L) = g) :
    AdjoinRoot f ≃ₐ[B] AdjoinRoot g :=
  AdjoinRoot.mapAlgEquiv σ f g (by
    rw [h])

/-- Residue algebras at ideals paired by a base-preserving automorphism
    are equivalent over the base ring. -/
noncomputable def conjugate_residue_algEquiv
    {B L : Type*} [CommRing B] [CommRing L] [Algebra B L]
    (σ : L ≃ₐ[B] L) (P : Ideal L) :
    (L ⧸ P) ≃ₐ[B] L ⧸ P.map (σ : L →+* L) :=
  Ideal.quotientEquivAlg P (P.map (σ : L →+* L)) σ rfl

/-- The transported residue algebras have the same base-module dimension. -/
theorem conjugate_residue_finrank_eq
    {B L : Type*} [CommRing B] [CommRing L] [Algebra B L]
    (σ : L ≃ₐ[B] L) (P : Ideal L) :
    Module.finrank B (L ⧸ P) =
      Module.finrank B (L ⧸ P.map (σ : L →+* L)) :=
  (conjugate_residue_algEquiv σ P).toLinearEquiv.finrank_eq

/-- An automorphism transports prime ideals to prime ideals. -/
theorem conjugate_prime_isPrime
    {B L : Type*} [CommRing B] [CommRing L] [Algebra B L]
    (σ : L ≃ₐ[B] L) (P : Ideal L) [P.IsPrime] :
    (P.map (σ : L →+* L)).IsPrime := by
  exact Ideal.map_isPrime_of_equiv σ

#print axioms conjugate_factor_identity
#print axioms conjugate_ideal_membership
#print axioms conjugate_quotient_equiv
#print axioms conjugate_quotient_algEquiv
#print axioms conjugate_residue_algEquiv
#print axioms conjugate_residue_finrank_eq
#print axioms conjugate_prime_isPrime

end J1728QuarticConjugacy
