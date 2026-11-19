import ProjectiveClassCoalescence
import Mathlib.Tactic

/-! A parametric family of coalescing chords whose source addition formula
has a growing common factor. -/
namespace XedniProjectiveCoalescenceFamily

open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

private def W (d : ℤ) : WeierstrassCurve ℤ := ⟨0, 0, 0, -(d ^ 2), 1⟩
private def f : ℤ →+* ZMod 5 := Int.castRingHom (ZMod 5)
private def P : Fin 3 → ℤ := ![0, 1, 1]
private def T (d : ℤ) : Fin 3 → ℤ := ![d, 1, 1]
private def U (d : ℤ) : Fin 3 → ℤ := ![-d, -1, 1]

theorem P_on_curve (d : ℤ) : WeierstrassCurve.Projective.Equation (W d) P := by
  norm_num [W, P, WeierstrassCurve.Projective.equation_iff,
    WeierstrassCurve.Projective.fin3_def_ext]

theorem T_on_curve (d : ℤ) : WeierstrassCurve.Projective.Equation (W d) (T d) := by
  norm_num [W, T, WeierstrassCurve.Projective.equation_iff,
    WeierstrassCurve.Projective.fin3_def_ext]
  ring

/-- The source chord vector has the exact factor `-d³`; the normalized
vector has unit projective `Z`. -/
theorem source_chord_factorization (d : ℤ) :
    WeierstrassCurve.Projective.addXYZ (W d) P (T d) =
      (-(d ^ 3)) • U d := by
  ext i
  fin_cases i <;> simp [W, P, T, U,
    WeierstrassCurve.Projective.addXYZ,
    WeierstrassCurve.Projective.addX,
    WeierstrassCurve.Projective.addY,
    WeierstrassCurve.Projective.negY,
    WeierstrassCurve.Projective.negAddY,
    WeierstrassCurve.Projective.addZ] <;> ring

theorem primitive_on_curve (d : ℤ) :
    WeierstrassCurve.Projective.Equation (W d) (U d) := by
  norm_num [W, U, WeierstrassCurve.Projective.equation_iff,
    WeierstrassCurve.Projective.fin3_def_ext]
  ring

theorem primitive_z_eq_one (d : ℤ) : (U d) 2 = 1 := by rfl

private theorem mapped_T_eq_P (d : ℤ) (hd : f d = 0) :
    f ∘ T d = f ∘ P := by
  change (d : ZMod 5) = 0 at hd
  ext i
  fin_cases i <;> simp [f, T, P, hd]

private theorem mapped_U_eq_zero_offset (d : ℤ) (hd : f d = 0) :
    f ∘ U d = f ∘ U 0 := by
  change (d : ZMod 5) = 0 at hd
  ext i
  fin_cases i <;> simp [f, U, hd]

private theorem mapped_W_eq_zero_offset (d : ℤ) (hd : f d = 0) :
    (W d).map f = (W 0).map f := by
  change (d : ZMod 5) = 0 at hd
  ext <;> simp [W, f, hd]

/-- The reduction is the same smooth curve for every offset divisible by 5. -/
theorem reduced_discriminant (d : ℤ) (hd : f d = 0) :
    ((W d).map f).Δ = (3 : ZMod 5) := by
  rw [mapped_W_eq_zero_offset d hd]
  norm_num [W, f, WeierstrassCurve.map_Δ, WeierstrassCurve.Δ,
    WeierstrassCurve.b₂, WeierstrassCurve.b₄,
    WeierstrassCurve.b₆, WeierstrassCurve.b₈]
  all_goals decide

theorem reduced_curve_elliptic (d : ℤ) (hd : f d = 0) :
    ((W d).map f).IsElliptic := by
  refine ⟨?_⟩
  rw [reduced_discriminant d hd]
  decide

/-- For every offset divisible by 5, the primitive source vector reduces to
the doubling class on the same smooth reduced curve. -/
theorem primitive_reduction_eq_double (d : ℤ) (hd : f d = 0) :
    mapClass f (⟦U d⟧ : WeierstrassCurve.Projective.PointClass ℤ) =
      WeierstrassCurve.Projective.addMap ((W d).map f)
        (mapClass f ⟦P⟧) (mapClass f ⟦T d⟧) := by
  rw [mapClass_mk, mapClass_mk, mapClass_mk,
    mapped_T_eq_P d hd, mapped_U_eq_zero_offset d hd,
    mapped_W_eq_zero_offset d hd]
  change (⟦f ∘ U 0⟧ : WeierstrassCurve.Projective.PointClass (ZMod 5)) =
    ⟦WeierstrassCurve.Projective.add ((W 0).map f) (f ∘ P) (f ∘ P)⟧
  rw [WeierstrassCurve.Projective.add_self]
  apply Quotient.sound
  have hv : WeierstrassCurve.Projective.dblXYZ ((W 0).map f) (f ∘ P) =
      (3 : ZMod 5) • (f ∘ U 0) := by
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
  exact WeierstrassCurve.Projective.smul_equiv (f ∘ U 0)
    (u := (3 : ZMod 5)) (by decide)

/-- Offsets `5^k` therefore give chord vectors with a factor `5^(3k)`;
the primitive vector retains `Z=1` for every `k`. -/
theorem power_family_factorization (k : ℕ) :
    WeierstrassCurve.Projective.addXYZ (W ((5 : ℤ) ^ k)) P (T ((5 : ℤ) ^ k)) =
      (-((5 : ℤ) ^ (3 * k))) • U ((5 : ℤ) ^ k) := by
  rw [source_chord_factorization]
  congr 1
  ring

theorem power_family_chord_z_exact (k : ℕ) :
    (WeierstrassCurve.Projective.addXYZ
      (W ((5 : ℤ) ^ k)) P (T ((5 : ℤ) ^ k))) 2 =
      -((5 : ℤ) ^ (3 * k)) := by
  rw [power_family_factorization]
  simp [U]

theorem power_family_source_distinct (k : ℕ) :
    ¬P ≈ T ((5 : ℤ) ^ (k + 1)) := by
  apply WeierstrassCurve.Projective.not_equiv_of_X_ne
  simpa [P, T] using
    (pow_ne_zero (k + 1) (by norm_num : (5 : ℤ) ≠ 0)).symm

private theorem power_offset_reduces_zero (k : ℕ) :
    f ((5 : ℤ) ^ (k + 1)) = 0 := by
  change (((5 : ℤ) ^ (k + 1) : ℤ) : ZMod 5) = 0
  have h5 : (5 : ZMod 5) = 0 := by decide
  simp [pow_succ, h5]

theorem power_family_primitive_reduction (k : ℕ) :
    mapClass f (⟦U ((5 : ℤ) ^ (k + 1))⟧ :
      WeierstrassCurve.Projective.PointClass ℤ) =
      WeierstrassCurve.Projective.addMap
        ((W ((5 : ℤ) ^ (k + 1))).map f)
        (mapClass f ⟦P⟧)
        (mapClass f ⟦T ((5 : ℤ) ^ (k + 1))⟧) :=
  primitive_reduction_eq_double _ (power_offset_reduces_zero k)

theorem power_family_reduced_curve_elliptic (k : ℕ) :
    ((W ((5 : ℤ) ^ (k + 1))).map f).IsElliptic :=
  reduced_curve_elliptic _ (power_offset_reduces_zero k)

theorem power_family_raw_mapClass_not_addMap (k : ℕ) :
    mapClass f (WeierstrassCurve.Projective.addMap
      (W ((5 : ℤ) ^ (k + 1)))
      (⟦P⟧ : WeierstrassCurve.Projective.PointClass ℤ)
      ⟦T ((5 : ℤ) ^ (k + 1))⟧) ≠
      WeierstrassCurve.Projective.addMap
        ((W ((5 : ℤ) ^ (k + 1))).map f)
        (mapClass f ⟦P⟧)
        (mapClass f ⟦T ((5 : ℤ) ^ (k + 1))⟧) := by
  apply XedniProjectiveClassCoalescence.mapClass_addMap_ne_addMap_of_equiv
    f _ P _ (power_family_source_distinct k)
  · rw [mapped_T_eq_P _ (power_offset_reduces_zero k)]
  · rw [mapped_W_eq_zero_offset _ (power_offset_reduces_zero k)]
    norm_num [W, f, P, WeierstrassCurve.Projective.dblXYZ,
      WeierstrassCurve.Projective.dblZ,
      WeierstrassCurve.Projective.negY]
    all_goals decide

#print axioms P_on_curve
#print axioms T_on_curve
#print axioms source_chord_factorization
#print axioms primitive_on_curve
#print axioms primitive_z_eq_one
#print axioms reduced_discriminant
#print axioms reduced_curve_elliptic
#print axioms primitive_reduction_eq_double
#print axioms power_family_factorization
#print axioms power_family_chord_z_exact
#print axioms power_family_source_distinct
#print axioms power_family_primitive_reduction
#print axioms power_family_reduced_curve_elliptic
#print axioms power_family_raw_mapClass_not_addMap

end XedniProjectiveCoalescenceFamily
