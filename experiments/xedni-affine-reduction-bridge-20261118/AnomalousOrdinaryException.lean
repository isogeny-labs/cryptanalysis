import RegularGroupLaw
import Mathlib.Tactic

/-!
The nonsingular curve y² = x³ + 3x + 2 over F₅ has exactly five group
points, including infinity. Its Frobenius trace is one, so the standard
finite-field trace criterion identifies it as ordinary. This exact curve
shows why an ordinary-curve statement must state any prime-to-p group-order
hypothesis separately.
-/

namespace XedniAnomalousOrdinaryException

open XedniRegularGroupLaw

local instance : Fact (Nat.Prime 5) := ⟨by norm_num⟩

def curve : WeierstrassCurve (ZMod 5) := shortCurve 3 2

/-- The discriminant is nonzero in F₅, so the actual affine curve is elliptic. -/
theorem curve_elliptic : curve.toAffine.IsElliptic := by
  rw [WeierstrassCurve.isElliptic_iff, isUnit_iff_ne_zero]
  norm_num [curve, shortCurve, WeierstrassCurve.Δ, WeierstrassCurve.b₂,
    WeierstrassCurve.b₄, WeierstrassCurve.b₆, WeierstrassCurve.b₈]
  decide

local instance : curve.toAffine.IsElliptic := curve_elliptic

def coordinatePredicate (xy : ZMod 5 × ZMod 5) : Prop :=
  xy.2 ^ 2 = xy.1 ^ 3 + 3 * xy.1 + 2

local instance : DecidablePred coordinatePredicate := by
  intro xy
  unfold coordinatePredicate
  infer_instance

/-- On this nonsingular curve, Mathlib's point predicate is the displayed
short-Weierstrass equation. -/
theorem nonsingular_iff_coordinates (xy : ZMod 5 × ZMod 5) :
    curve.toAffine.Nonsingular xy.1 xy.2 ↔ coordinatePredicate xy := by
  rw [← WeierstrassCurve.Affine.equation_iff_nonsingular]
  rw [WeierstrassCurve.Affine.equation_iff]
  simp [curve, shortCurve, coordinatePredicate]

private def coordinateEquiv :
    {xy : ZMod 5 × ZMod 5 // curve.toAffine.Nonsingular xy.1 xy.2} ≃
      {xy : ZMod 5 × ZMod 5 // coordinatePredicate xy} :=
  Equiv.subtypeEquivProp
    (by funext xy; exact propext (nonsingular_iff_coordinates xy))

local instance : Fintype
    {xy : ZMod 5 × ZMod 5 // curve.toAffine.Nonsingular xy.1 xy.2} :=
  Fintype.ofEquiv {xy : ZMod 5 × ZMod 5 // coordinatePredicate xy}
    coordinateEquiv.symm

local instance : Fintype
    (WithZero {xy : ZMod 5 × ZMod 5 // curve.toAffine.Nonsingular xy.1 xy.2}) :=
  (inferInstance : Fintype
    (Option {xy : ZMod 5 × ZMod 5 // curve.toAffine.Nonsingular xy.1 xy.2}))

local instance : Fintype curve.toAffine.Point :=
  Fintype.ofEquiv
    (WithZero {xy : ZMod 5 × ZMod 5 // curve.toAffine.Nonsingular xy.1 xy.2})
    (curve.toAffine.nonsingularPointEquiv).symm

/-- The actual elliptic-curve point group has four affine points and infinity. -/
theorem curve_group_card : Fintype.card curve.toAffine.Point = 5 := by
  calc
    Fintype.card curve.toAffine.Point =
        Fintype.card
          (WithZero {xy : ZMod 5 × ZMod 5 // curve.toAffine.Nonsingular xy.1 xy.2}) :=
      Fintype.card_congr curve.toAffine.nonsingularPointEquiv
    _ = Fintype.card
          {xy : ZMod 5 × ZMod 5 // curve.toAffine.Nonsingular xy.1 xy.2} + 1 :=
      Fintype.card_option
    _ = Fintype.card
          {xy : ZMod 5 × ZMod 5 // coordinatePredicate xy} + 1 := by
      rw [Fintype.card_congr coordinateEquiv]
    _ = 5 := by
      rw [Fintype.card_subtype]
      decide

/-- The group order equals the field prime. -/
theorem anomalous_order : 5 ∣ Fintype.card curve.toAffine.Point := by
  rw [curve_group_card]

/-- With #E(F₅)=5, the Frobenius trace 5+1-#E(F₅) is one. -/
theorem trace_one : 5 + 1 - Fintype.card curve.toAffine.Point = 1 := by
  rw [curve_group_card]

#print axioms XedniAnomalousOrdinaryException.curve_elliptic
#print axioms XedniAnomalousOrdinaryException.nonsingular_iff_coordinates
#print axioms XedniAnomalousOrdinaryException.curve_group_card
#print axioms XedniAnomalousOrdinaryException.anomalous_order
#print axioms XedniAnomalousOrdinaryException.trace_one

end XedniAnomalousOrdinaryException
