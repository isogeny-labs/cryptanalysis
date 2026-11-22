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

namespace XedniCanonicalLiftDefect

variable {G L : Type*} [AddCommGroup G] [AddCommGroup L]

/-- The additive defect of an arbitrary selected lift. -/
def defect (lift : G → L) (x y : G) : L :=
  lift (x + y) - lift x - lift y

/-- An exact section's additive defect lies in the reduction kernel. -/
theorem defect_reduces_to_zero (reduce : L →+ G) (lift : G → L)
    (hsection : ∀ x, reduce (lift x) = x) (x y : G) :
    reduce (defect lift x y) = 0 := by
  simp [defect, hsection]

/-- Additive defects satisfy the cocycle identity for every selected lift. -/
theorem defect_cocycle (lift : G → L) (x y z : G) :
    defect lift x y + defect lift (x + y) z =
      defect lift y z + defect lift x (y + z) := by
  simp only [defect, add_assoc]
  abel

/-- A selected lift is additive exactly when all its defects vanish. -/
theorem defect_zero_iff_additive (lift : G → L) :
    (∀ x y, defect lift x y = 0) ↔
      (∀ x y, lift (x + y) = lift x + lift y) := by
  constructor
  · intro h x y
    have := h x y
    dsimp [defect] at this
    have hxy : lift (x + y) - lift x = lift y := sub_eq_zero.mp this
    have hsum : lift (x + y) = lift y + lift x := sub_eq_iff_eq_add.mp hxy
    simpa only [add_comm] using hsum
  · intro h x y
    simp [defect, h x y]

#print axioms XedniCanonicalLiftDefect.defect_reduces_to_zero
#print axioms XedniCanonicalLiftDefect.defect_cocycle
#print axioms XedniCanonicalLiftDefect.defect_zero_iff_additive

end XedniCanonicalLiftDefect
