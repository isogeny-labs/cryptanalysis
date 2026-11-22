import ProjectiveAddMapDistinct
import Mathlib.Tactic

/-! A smooth-reduction example in which raw projective `addMap` over `ℤ`
does not commute with coefficient reduction. The polynomial source addition
representative has a common factor of 5 and reduces to the zero vector,
while addition of the reduced points uses the doubling branch. -/
namespace XedniProjectiveAddMapCounterexample

open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

private def W : WeierstrassCurve ℤ := ⟨0, 0, 0, -25, 1⟩
private def f : ℤ →+* ZMod 5 := Int.castRingHom (ZMod 5)
private def P : Fin 3 → ℤ := ![0, 1, 1]
private def T : Fin 3 → ℤ := ![5, 1, 1]

theorem P_on_curve : WeierstrassCurve.Projective.Equation W P := by
  norm_num [W, P, WeierstrassCurve.Projective.equation_iff,
    WeierstrassCurve.Projective.fin3_def_ext]

theorem T_on_curve : WeierstrassCurve.Projective.Equation W T := by
  norm_num [W, T, WeierstrassCurve.Projective.equation_iff,
    WeierstrassCurve.Projective.fin3_def_ext]

/-- The reduced curve has nonzero discriminant in `ZMod 5`. -/
theorem reduced_discriminant : (W.map f).Δ = (3 : ZMod 5) := by
  norm_num [W, f, WeierstrassCurve.map_Δ, WeierstrassCurve.Δ,
    WeierstrassCurve.b₂, WeierstrassCurve.b₄,
    WeierstrassCurve.b₆, WeierstrassCurve.b₈]
  all_goals decide

theorem reduced_curve_elliptic : (W.map f).IsElliptic := by
  refine ⟨?_⟩
  rw [reduced_discriminant]
  decide

/-- Exact unnormalized source chord coordinates. -/
theorem source_addXYZ_exact :
    WeierstrassCurve.Projective.addXYZ W P T = ![625, 125, -125] := by
  ext i
  fin_cases i <;> norm_num [W, P, T,
    WeierstrassCurve.Projective.addXYZ,
    WeierstrassCurve.Projective.addX,
    WeierstrassCurve.Projective.addY,
    WeierstrassCurve.Projective.negY,
    WeierstrassCurve.Projective.negAddY,
    WeierstrassCurve.Projective.addZ]

/-- The raw source chord branch has a common factor of 5 and its
coordinatewise reduction is the zero vector. -/
theorem reduced_source_add_vector_zero :
    f ∘ WeierstrassCurve.Projective.add W P T = ![0, 0, 0] := by
  have hne : ¬P ≈ T := by
    apply WeierstrassCurve.Projective.not_equiv_of_X_ne
    norm_num [P, T]
  rw [WeierstrassCurve.Projective.add_of_not_equiv hne, source_addXYZ_exact]
  ext i
  fin_cases i <;> norm_num [f] <;> decide

private theorem mapped_points_eq : f ∘ P = f ∘ T := by
  ext i
  fin_cases i <;> norm_num [f, P, T]
  all_goals decide

private theorem reduced_double_z_ne_zero :
    (WeierstrassCurve.Projective.dblXYZ (W.map f) (f ∘ P)) 2 ≠ 0 := by
  norm_num [W, f, P, WeierstrassCurve.Projective.dblXYZ,
    WeierstrassCurve.Projective.dblZ,
    WeierstrassCurve.Projective.negY]
  all_goals decide

/-- Raw projective class reduction fails to preserve `addMap` for these
coalescing source points, even though the reduced curve is elliptic. -/
theorem raw_mapClass_not_addMap :
    mapClass f (WeierstrassCurve.Projective.addMap W
      (⟦P⟧ : WeierstrassCurve.Projective.PointClass ℤ) ⟦T⟧) ≠
    WeierstrassCurve.Projective.addMap (W.map f)
      (mapClass f ⟦P⟧) (mapClass f ⟦T⟧) := by
  intro heq
  have hleft : mapClass f (WeierstrassCurve.Projective.addMap W
      (⟦P⟧ : WeierstrassCurve.Projective.PointClass ℤ) ⟦T⟧) =
      (⟦![0, 0, 0]⟧ : WeierstrassCurve.Projective.PointClass (ZMod 5)) := by
    change (⟦f ∘ WeierstrassCurve.Projective.add W P T⟧ :
      WeierstrassCurve.Projective.PointClass (ZMod 5)) = ⟦![0, 0, 0]⟧
    rw [reduced_source_add_vector_zero]
  have hright : WeierstrassCurve.Projective.addMap (W.map f)
      (mapClass f ⟦P⟧) (mapClass f ⟦T⟧) =
      (⟦WeierstrassCurve.Projective.dblXYZ (W.map f) (f ∘ P)⟧ :
        WeierstrassCurve.Projective.PointClass (ZMod 5)) := by
    change (⟦WeierstrassCurve.Projective.add (W.map f)
      (f ∘ P) (f ∘ T)⟧ :
      WeierstrassCurve.Projective.PointClass (ZMod 5)) = _
    rw [← mapped_points_eq, WeierstrassCurve.Projective.add_self]
  rw [hleft, hright] at heq
  have hnot : ¬(![0, 0, 0] : Fin 3 → ZMod 5) ≈
      WeierstrassCurve.Projective.dblXYZ (W.map f) (f ∘ P) :=
    WeierstrassCurve.Projective.not_equiv_of_Z_eq_zero_left
      (by simp) reduced_double_z_ne_zero
  exact hnot (Quotient.eq.mp heq)

#print axioms P_on_curve
#print axioms T_on_curve
#print axioms reduced_discriminant
#print axioms reduced_curve_elliptic
#print axioms source_addXYZ_exact
#print axioms reduced_source_add_vector_zero
#print axioms raw_mapClass_not_addMap

end XedniProjectiveAddMapCounterexample
