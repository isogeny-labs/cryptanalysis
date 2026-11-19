import Mathlib

/-!
An additive logarithm with torsion-free codomain annihilates the image of a
homomorphic lift of a finite subgroup.  The statement does not assume that
an elliptic-curve logarithm is defined on the entire lifted curve: `log` is
an explicitly supplied additive homomorphism on the indicated lift group.
-/

namespace XedniCanonicalLiftTorsionObstruction

variable {G L A : Type*}
variable [AddGroup G] [Finite G] [AddGroup L] [AddGroup A] [IsAddTorsionFree A]

/-- Every additive map from a finite group to a torsion-free additive group is zero. -/
theorem finite_log_zero (f : G →+ A) (x : G) : f x = 0 := by
  obtain ⟨n, hn, hx0⟩ :=
    (isOfFinAddOrder_iff_nsmul_eq_zero).mp (isOfFinAddOrder_of_finite x)
  have hfx0 : n • f x = 0 := by
    rw [← map_nsmul]
    simp [hx0]
  have hx : IsOfFinAddOrder (f x) :=
    (isOfFinAddOrder_iff_nsmul_eq_zero).mpr ⟨n, hn, hfx0⟩
  exact (isOfFinAddOrder_iff_eq_zero (f x)).mp hx

/-- A homomorphic lift followed by an additive logarithm gives zero on every
finite-subgroup input. -/
theorem homomorphic_lift_log_zero (lift : G →+ L) (log : L →+ A) (x : G) :
    log (lift x) = 0 := by
  exact finite_log_zero (log.comp lift) x

/-- A homomorphic section into a torsion-free lift group forces the finite
source group to be trivial. -/
theorem torsion_free_section_trivial [IsAddTorsionFree L]
    (reduce : L →+ G) (lift : G →+ L)
    (hsection : reduce.comp lift = AddMonoidHom.id G) (x : G) : x = 0 := by
  have hx : lift x = 0 := finite_log_zero lift x
  have h : reduce (lift x) = x := by
    have := congrArg (fun f : G →+ G => f x) hsection
    simpa only [AddMonoidHom.comp_apply, AddMonoidHom.id_apply] using this
  simpa [hx] using h.symm

/-- Every set-theoretic section from a nontrivial finite group into a
torsion-free additive group has a concrete additive defect. -/
theorem section_has_additive_defect [IsAddTorsionFree L] [Nontrivial G]
    (reduce : L →+ G) (lift : G → L)
    (hsection : ∀ x, reduce (lift x) = x) :
    ∃ x y : G, lift (x + y) ≠ lift x + lift y := by
  by_contra h
  push Not at h
  have hzero : lift 0 = 0 := by
    have hz := h 0 0
    simp only [zero_add] at hz
    apply add_left_cancel (a := lift 0)
    simpa using hz.symm
  let liftHom : G →+ L :=
    { toFun := lift
      map_zero' := hzero
      map_add' := h }
  have hcomp : reduce.comp liftHom = AddMonoidHom.id G := by
    ext x
    exact hsection x
  obtain ⟨x, hx⟩ := exists_ne (0 : G)
  exact hx (torsion_free_section_trivial reduce liftHom hcomp x)

#print axioms XedniCanonicalLiftTorsionObstruction.finite_log_zero
#print axioms XedniCanonicalLiftTorsionObstruction.homomorphic_lift_log_zero
#print axioms XedniCanonicalLiftTorsionObstruction.torsion_free_section_trivial
#print axioms XedniCanonicalLiftTorsionObstruction.section_has_additive_defect

end XedniCanonicalLiftTorsionObstruction
