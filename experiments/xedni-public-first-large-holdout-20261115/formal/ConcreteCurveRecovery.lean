import DistinctOffsetRecovery
import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point

namespace XedniPublicFirstLargeHoldout

/-- The exact reduced Weierstrass model used in the finite-field panel. -/
def panelCurve (p : ℕ) : WeierstrassCurve.Affine (ZMod p) :=
  ⟨0, 0, 0, -1, -2⟩

theorem panelCurve_discriminant (p : ℕ) :
    (panelCurve p).Δ = (-1664 : ZMod p) := by
  norm_num [panelCurve, WeierstrassCurve.Δ, WeierstrassCurve.b₂,
    WeierstrassCurve.b₄, WeierstrassCurve.b₆, WeierstrassCurve.b₈]

theorem panelCurve_isElliptic (p : ℕ) [Fact p.Prime]
    (hp : ¬ p ∣ 1664) : (panelCurve p).IsElliptic := by
  have hne : (1664 : ZMod p) ≠ 0 := by
    intro h
    exact hp ((ZMod.natCast_eq_zero_iff 1664 p).mp h)
  refine ⟨isUnit_iff_ne_zero.mpr ?_⟩
  rw [panelCurve_discriminant]
  exact neg_ne_zero.mpr hne

/-- The affine point (2,2) on the exact reduced model. -/
def panelGenerator (p : ℕ) [Fact p.Prime] (hp : ¬ p ∣ 1664) :
    (panelCurve p).Point := by
  letI : (panelCurve p).IsElliptic := panelCurve_isElliptic p hp
  exact WeierstrassCurve.Affine.Point.mk (x := (2 : ZMod p)) (y := (2 : ZMod p)) (by
    simp only [panelCurve, WeierstrassCurve.Affine.equation_iff]
    norm_num)

theorem panelGenerator_nonzero (p : ℕ) [Fact p.Prime]
    (hp : ¬ p ∣ 1664) : panelGenerator p hp ≠ 0 := by
  letI : (panelCurve p).IsElliptic := panelCurve_isElliptic p hp
  intro h
  have heq := congrArg (WeierstrassCurve.Affine.pointEquiv (panelCurve p)) h
  simp only [panelGenerator, WeierstrassCurve.Affine.pointEquiv_some,
    WeierstrassCurve.Affine.Point.zero_def,
    WeierstrassCurve.Affine.pointEquiv_zero] at heq
  cases heq

/-- On the exact curve point type, a distinct-offset public relation is a
direct scalar-recovery certificate once the generator-order receipt is supplied. -/
theorem panel_curve_public_relation_iff_recovery
    (p q : ℕ) [Fact p.Prime] [Fact q.Prime]
    (hp : ¬ p ∣ 1664)
    (hq : q • panelGenerator p hp = 0)
    (a b w t₁ t₂ : ZMod q) (ha : a ≠ 0) (ht : t₁ ≠ t₂) :
    TorsionPublicRelation q
        (cyclic_torsion q (panelGenerator p hp) hq)
        ⟨panelGenerator p hp, AddSubgroup.mem_zmultiples _⟩
        a b w t₁ t₂ ↔
      a + b ≠ 0 ∧ w = (a * t₁ + b * t₂) / (a + b) := by
  let G := panelGenerator p hp
  letI : Module (ZMod q) (AddSubgroup.zmultiples G) :=
    AddCommGroup.zmodModule (cyclic_torsion q G hq)
  have hGsub : (⟨G, AddSubgroup.mem_zmultiples G⟩ : AddSubgroup.zmultiples G) ≠ 0 := by
    intro h
    exact panelGenerator_nonzero p hp (congrArg Subtype.val h)
  unfold TorsionPublicRelation
  exact distinct_offset_public_relation_iff_recovery q
    (⟨G, AddSubgroup.mem_zmultiples G⟩ : AddSubgroup.zmultiples G)
    hGsub a b w t₁ t₂ ha ht

#print axioms panelCurve_discriminant
#print axioms panelCurve_isElliptic
#print axioms panelGenerator_nonzero
#print axioms panel_curve_public_relation_iff_recovery

end XedniPublicFirstLargeHoldout
