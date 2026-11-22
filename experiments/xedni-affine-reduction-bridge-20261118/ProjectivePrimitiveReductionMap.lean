import ProjectivePrimitiveExistence
import Mathlib.Tactic

/-! A nonzero rational projective class admits primitive integral coordinates.
Reduction of those coordinates is independent of the choice and remains
nonzero over every nontrivial residue ring. -/
namespace XedniProjectivePrimitiveReductionMap

open XedniProjectivePrimitiveExistence
open XedniProjectivePrimitiveUniqueness
open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

private def q : ℤ →+* ℚ := Int.castRingHom ℚ

/-- Projective classes represented by a nonzero triple. -/
def NonzeroClass (R : Type*) [CommRing R] :=
  {C : PointClass R // C ≠ (⟦(0 : Fin 3 → R)⟧ : PointClass R)}

private theorem out_ne_zero (C : NonzeroClass ℚ) :
    Quotient.out C.val ≠ (0 : Fin 3 → ℚ) := by
  intro hzero
  apply C.property
  calc
    C.val = (⟦Quotient.out C.val⟧ : PointClass ℚ) := (Quotient.out_eq C.val).symm
    _ = ⟦(0 : Fin 3 → ℚ)⟧ := by rw [hzero]

/-- A chosen primitive integral representative of a nonzero rational class. -/
noncomputable def representative (C : NonzeroClass ℚ) : Fin 3 → ℤ :=
  Classical.choose (exists_primitive_rational_representative
    (Quotient.out C.val) (out_ne_zero C))

theorem representative_primitive (C : NonzeroClass ℚ) :
    Primitive (representative C) :=
  (Classical.choose_spec (exists_primitive_rational_representative
    (Quotient.out C.val) (out_ne_zero C))).1

theorem representative_class (C : NonzeroClass ℚ) :
    mapClass q (⟦representative C⟧ : PointClass ℤ) = C.val := by
  have h := (Classical.choose_spec (exists_primitive_rational_representative
    (Quotient.out C.val) (out_ne_zero C))).2
  change (Quotient.out C.val) ≈ (q ∘ representative C) at h
  change (⟦q ∘ representative C⟧ : PointClass ℚ) = C.val
  calc
    (⟦q ∘ representative C⟧ : PointClass ℚ) = ⟦Quotient.out C.val⟧ :=
      Quotient.eq.mpr (Setoid.symm h)
    _ = C.val := Quotient.out_eq C.val

/-- Reduction of a rational projective class through primitive integral
coordinates. -/
noncomputable def reduceClass {S : Type*} [CommRing S]
    (g : ℤ →+* S) (C : NonzeroClass ℚ) : PointClass S :=
  mapClass g (⟦representative C⟧ : PointClass ℤ)

/-- Any primitive integral representative gives the same reduced class. -/
theorem reduceClass_eq_of_rep {S : Type*} [CommRing S]
    (g : ℤ →+* S) (C : NonzeroClass ℚ) (U : Fin 3 → ℤ)
    (hU : Primitive U)
    (hClass : mapClass q (⟦U⟧ : PointClass ℤ) = C.val) :
    reduceClass g C = mapClass g (⟦U⟧ : PointClass ℤ) := by
  exact primitive_reduction_independent g (representative C) U
    (representative_primitive C) hU ((representative_class C).trans hClass.symm)

/-- The reduced class has a nonzero representative over any nontrivial ring. -/
theorem reduceClass_ne_zero {S : Type*} [CommRing S] [Nontrivial S]
    (g : ℤ →+* S) (C : NonzeroClass ℚ) :
    reduceClass g C ≠ (⟦(0 : Fin 3 → S)⟧ : PointClass S) := by
  intro hzero
  have hvec := primitive_map_ne_zero g (representative C)
    (representative_primitive C)
  change (⟦g ∘ representative C⟧ : PointClass S) = ⟦(0 : Fin 3 → S)⟧ at hzero
  obtain ⟨u, hu⟩ := Quotient.eq.mp hzero
  apply hvec
  have hz : u • (0 : Fin 3 → S) = 0 := by simp
  exact hu.symm.trans hz

/-- The choice-independent reduction map between nonzero projective classes. -/
noncomputable def reduceNonzero {S : Type*} [CommRing S] [Nontrivial S]
    (g : ℤ →+* S) : NonzeroClass ℚ → NonzeroClass S :=
  fun C => ⟨reduceClass g C, reduceClass_ne_zero g C⟩

theorem reduceNonzero_eq_of_rep {S : Type*} [CommRing S] [Nontrivial S]
    (g : ℤ →+* S) (C : NonzeroClass ℚ) (U : Fin 3 → ℤ)
    (hU : Primitive U)
    (hClass : mapClass q (⟦U⟧ : PointClass ℤ) = C.val) :
    (reduceNonzero g C).val = mapClass g (⟦U⟧ : PointClass ℤ) :=
  reduceClass_eq_of_rep g C U hU hClass

#print axioms representative_primitive
#print axioms representative_class
#print axioms reduceClass_eq_of_rep
#print axioms reduceClass_ne_zero
#print axioms reduceNonzero_eq_of_rep

end XedniProjectivePrimitiveReductionMap
