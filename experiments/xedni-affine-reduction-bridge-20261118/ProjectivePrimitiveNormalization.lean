import ProjectiveAddMapCounterexample
import Mathlib.Tactic

/-! The source chord polynomial in the coalescing example has a common
nonunit factor.  Its primitive vector is a regular integral point, and its
reduction represents the reduced doubling class. -/
namespace XedniProjectivePrimitiveNormalization

open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

private def W : WeierstrassCurve ℤ := ⟨0, 0, 0, -25, 1⟩
private def f : ℤ →+* ZMod 5 := Int.castRingHom (ZMod 5)
private def P : Fin 3 → ℤ := ![0, 1, 1]
private def T : Fin 3 → ℤ := ![5, 1, 1]
private def U : Fin 3 → ℤ := ![-5, -1, 1]

/-- Exact removal of the common nonunit factor from the source chord. -/
theorem source_chord_factorization :
    WeierstrassCurve.Projective.addXYZ W P T = (-125 : ℤ) • U := by
  ext i
  fin_cases i <;> norm_num [W, P, T, U,
    WeierstrassCurve.Projective.addXYZ,
    WeierstrassCurve.Projective.addX,
    WeierstrassCurve.Projective.addY,
    WeierstrassCurve.Projective.negY,
    WeierstrassCurve.Projective.negAddY,
    WeierstrassCurve.Projective.addZ]

/-- The primitive vector is an integral projective point with unit Z-coordinate. -/
theorem primitive_on_curve : WeierstrassCurve.Projective.Equation W U := by
  norm_num [W, U, WeierstrassCurve.Projective.equation_iff,
    WeierstrassCurve.Projective.fin3_def_ext]

theorem primitive_z_eq_one : U 2 = 1 := by rfl

private theorem mapped_points_eq : f ∘ P = f ∘ T := by
  ext i
  fin_cases i <;> norm_num [f, P, T]
  all_goals decide

/-- The normalized source point reduces to the same projective class as
doubling the reduced input on the smooth reduced curve. -/
theorem primitive_reduction_eq_double :
    mapClass f (⟦U⟧ : WeierstrassCurve.Projective.PointClass ℤ) =
      WeierstrassCurve.Projective.addMap (W.map f)
        (mapClass f ⟦P⟧) (mapClass f ⟦T⟧) := by
  change (⟦f ∘ U⟧ : WeierstrassCurve.Projective.PointClass (ZMod 5)) =
    ⟦WeierstrassCurve.Projective.add (W.map f) (f ∘ P) (f ∘ T)⟧
  rw [← mapped_points_eq, WeierstrassCurve.Projective.add_self]
  apply Quotient.sound
  -- The two representatives differ by a nonzero residue scalar.
  have hv : WeierstrassCurve.Projective.dblXYZ (W.map f) (f ∘ P) =
      (3 : ZMod 5) • (f ∘ U) := by
    ext i
    fin_cases i <;> norm_num [W, f, P, U,
      WeierstrassCurve.Projective.dblXYZ,
      WeierstrassCurve.Projective.dblX,
      WeierstrassCurve.Projective.dblY,
      WeierstrassCurve.Projective.dblZ,
      WeierstrassCurve.Projective.negY,
      WeierstrassCurve.Projective.negDblY]
    all_goals decide
  rw [hv]
  symm
  exact WeierstrassCurve.Projective.smul_equiv (f ∘ U) (u := (3 : ZMod 5)) (by decide)

#print axioms source_chord_factorization
#print axioms primitive_on_curve
#print axioms primitive_z_eq_one
#print axioms primitive_reduction_eq_double

end XedniProjectivePrimitiveNormalization
