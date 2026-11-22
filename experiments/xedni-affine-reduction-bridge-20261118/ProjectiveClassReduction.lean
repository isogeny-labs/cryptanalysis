import ResidueAdditionZero
import Mathlib.Tactic

/-! Ring homomorphisms induce maps on projective point classes because they
send unit-scaled representatives to unit-scaled representatives. The
residue-vertical source addition class maps to the reduced zero class. -/
namespace XedniProjectiveClassReduction

open XedniRegularChainReduction XedniRegularGroupLaw XedniSourceChordAddition
open XedniResidueAdditionZero
open WeierstrassCurve.Projective

variable {R S : Type*} [CommRing R] [CommRing S]

/-- Coordinatewise application of a ring homomorphism preserves projective
equivalence, including over source rings with zero divisors. -/
theorem map_equiv (f : R →+* S) {P Q : Fin 3 → R} (h : P ≈ Q) :
    f ∘ P ≈ f ∘ Q := by
  rcases h with ⟨u, rfl⟩
  exact ⟨Units.map f u, (WeierstrassCurve.Projective.comp_smul ..).symm⟩

/-- The well-defined map of projective point classes induced by a ring
homomorphism. -/
def mapClass (f : R →+* S) :
    WeierstrassCurve.Projective.PointClass R →
      WeierstrassCurve.Projective.PointClass S :=
  Quotient.map (fun P : Fin 3 → R => f ∘ P) (fun _ _ h => map_equiv f h)

@[simp]
theorem mapClass_mk (f : R →+* S) (P : Fin 3 → R) :
    mapClass f (⟦P⟧ : WeierstrassCurve.Projective.PointClass R) =
      (⟦f ∘ P⟧ : WeierstrassCurve.Projective.PointClass S) := rfl

variable {F : Type*} [Field F]
variable (f : R →+* F) {A B : R}

/-- The source projective addition class maps to the reduced zero class at
the residue-vertical chord. The source addition is the actual mathlib
`addMap` operation on projective classes. -/
theorem mapClass_source_addMap_eq_zero (P T : CurvePoint R A B)
    (hx : f (T.x - P.x) = 0) (hy : f (T.y - P.y) ≠ 0) :
    mapClass f
      (WeierstrassCurve.Projective.addMap
        (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
        (⟦affineTriple P⟧ : WeierstrassCurve.Projective.PointClass R)
        (⟦affineTriple T⟧ : WeierstrassCurve.Projective.PointClass R)) =
      (⟦![0, 1, 0]⟧ : WeierstrassCurve.Projective.PointClass F) := by
  change (⟦f ∘ WeierstrassCurve.Projective.add
    (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
    (affineTriple P) (affineTriple T)⟧ :
    WeierstrassCurve.Projective.PointClass F) = ⟦![0, 1, 0]⟧
  exact reduced_source_add_class_eq_zero f P T hx hy

private theorem reduced_affine_equation (P : CurvePoint R A B) :
    WeierstrassCurve.Projective.Equation (shortCurve (f A) (f B))
      (f ∘ affineTriple P) := by
  classical
  have hcoord : f ∘ affineTriple P = ![f P.x, f P.y, 1] := by
    ext i
    fin_cases i <;> simp [affineTriple]
  rw [hcoord]
  exact (WeierstrassCurve.Projective.equation_some _ _).mpr
    (short_equation (mapPoint f P))

/-- Reduction commutes with projective point-class addition at a
residue-vertical chord with nonzero reduced y-difference. Both sides are the
zero class, with the source branch and the residue branch proved separately. -/
theorem mapClass_addMap_residue_vertical (P T : CurvePoint R A B)
    (hx : f (T.x - P.x) = 0) (hy : f (T.y - P.y) ≠ 0) :
    mapClass f
      (WeierstrassCurve.Projective.addMap
        (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
        (⟦affineTriple P⟧ : WeierstrassCurve.Projective.PointClass R)
        (⟦affineTriple T⟧ : WeierstrassCurve.Projective.PointClass R)) =
      WeierstrassCurve.Projective.addMap (shortCurve (f A) (f B))
        (mapClass f (⟦affineTriple P⟧ : WeierstrassCurve.Projective.PointClass R))
        (mapClass f (⟦affineTriple T⟧ : WeierstrassCurve.Projective.PointClass R)) := by
  classical
  let U := f ∘ affineTriple P
  let V := f ∘ affineTriple T
  have hU : WeierstrassCurve.Projective.Equation (shortCurve (f A) (f B)) U :=
    reduced_affine_equation f P
  have hV : WeierstrassCurve.Projective.Equation (shortCurve (f A) (f B)) V :=
    reduced_affine_equation f T
  have hUz : U 2 ≠ 0 := by simp [U, affineTriple]
  have hVz : V 2 ≠ 0 := by simp [V, affineTriple]
  have hX : U 0 * V 2 = V 0 * U 2 := by
    have hx' : f T.x = f P.x := by
      simpa only [map_sub, sub_eq_zero] using hx
    simp [U, V, affineTriple, hx']
  have hY : U 1 * V 2 ≠ V 1 * U 2 := by
    have hy' : f T.y ≠ f P.y := by
      simpa only [map_sub, sub_ne_zero] using hy
    simpa [U, V, affineTriple] using hy'.symm
  have hadd := WeierstrassCurve.Projective.add_of_Y_ne
    (W := shortCurve (f A) (f B)) hU hV hUz hVz hX hY
  have hunit : IsUnit (WeierstrassCurve.Projective.addU U V) :=
    WeierstrassCurve.Projective.isUnit_addU_of_Y_ne hUz hVz hY
  have hrhs :
      WeierstrassCurve.Projective.addMap (shortCurve (f A) (f B))
        (⟦U⟧ : WeierstrassCurve.Projective.PointClass F)
        (⟦V⟧ : WeierstrassCurve.Projective.PointClass F) =
        (⟦![0, 1, 0]⟧ : WeierstrassCurve.Projective.PointClass F) := by
    change (⟦WeierstrassCurve.Projective.add (shortCurve (f A) (f B)) U V⟧ :
      WeierstrassCurve.Projective.PointClass F) = ⟦![0, 1, 0]⟧
    rw [hadd]
    exact WeierstrassCurve.Projective.smul_eq ![0, 1, 0] hunit
  rw [mapClass_mk, mapClass_mk]
  change mapClass f
      (WeierstrassCurve.Projective.addMap
        (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
        (⟦affineTriple P⟧ : WeierstrassCurve.Projective.PointClass R)
        (⟦affineTriple T⟧ : WeierstrassCurve.Projective.PointClass R)) =
    WeierstrassCurve.Projective.addMap (shortCurve (f A) (f B))
      (⟦U⟧ : WeierstrassCurve.Projective.PointClass F) ⟦V⟧
  exact (mapClass_source_addMap_eq_zero f P T hx hy).trans hrhs.symm

#print axioms map_equiv
#print axioms mapClass_mk
#print axioms mapClass_source_addMap_eq_zero
#print axioms mapClass_addMap_residue_vertical

end XedniProjectiveClassReduction
