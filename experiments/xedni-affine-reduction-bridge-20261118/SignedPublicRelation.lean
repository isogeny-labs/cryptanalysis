import PublicPointReduction

namespace XedniSignedPublicRelation

open XedniLocalZModReduction XedniRegularChainReduction
open XedniRegularGroupLaw XedniCurveEquationCertificates
open XedniExactChainMultipliers XedniFiniteGroupChains
open XedniPublicPointReduction
open XedniRecordedRegularSteps

local instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 421) := ⟨by norm_num⟩
local instance :
    (shortCurve
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) (-1)))
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) 15961))).IsElliptic :=
  row0_reduced_elliptic
local instance :
    (shortCurve
      (reduceZMod 421 ((algebraMap ℤ (localIntegers 421)) (-1)))
      (reduceZMod 421 ((algebraMap ℤ (localIntegers 421)) 9273786))).IsElliptic :=
  row1_reduced_elliptic

theorem curvePoint_ext {F : Type*} [Field F] {A B : F}
    {P Q : CurvePoint F A B} (hx : P.x = Q.x) (hy : P.y = Q.y) : P = Q := by
  cases P with
  | mk px py hp =>
    cases Q with
    | mk qx qy hq =>
      cases hx
      cases hy
      rfl

def pointCoords {F : Type*} [Field F] {A B : F}
    [(shortCurve A B).IsElliptic]
    (P : (shortCurve A B).toAffine.Point) : Option (F × F) :=
  match P with
  | .zero => none
  | .some x y _ => some (x, y)

theorem pointCoords_toGroupPoint {F : Type*} [Field F] [DecidableEq F]
    {A B : F} [(shortCurve A B).IsElliptic] (P : CurvePoint F A B) :
    pointCoords (toGroupPoint P) = some (P.x, P.y) := rfl

theorem pointCoords_neg_toGroupPoint {F : Type*} [Field F] [DecidableEq F]
    {A B : F} [(shortCurve A B).IsElliptic] (P : CurvePoint F A B) :
    pointCoords (-toGroupPoint P) = some (P.x, -P.y) := by
  unfold toGroupPoint
  simp only [WeierstrassCurve.Affine.Point.mk]
  rw [WeierstrassCurve.Affine.Point.neg_some]
  simp [pointCoords, shortCurve, WeierstrassCurve.Affine.negY]

theorem signed_multiple_relation {G : Type*} [AddCommGroup G]
    (R : G) (a b : ℤ) :
    a • (b • R) + b • ((-a) • R) = 0 := by
  rw [smul_smul, smul_smul, ← add_smul]
  have hz : a * b + b * -a = 0 := by ring
  rw [hz, zero_smul]

private def row0_publicU :
    CurvePoint (ZMod 313)
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) (-1)))
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) 15961)) := by
  refine ⟨306, 125, ?_⟩
  norm_num [reduce_integer, map_ofNat] <;> decide

private def row0_publicV :
    CurvePoint (ZMod 313)
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) (-1)))
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) 15961)) := by
  refine ⟨1, 130, ?_⟩
  norm_num [reduce_integer, map_ofNat] <;> decide

theorem row0_U_eq :
    toGroupPoint row0_publicU =
      toGroupPoint (mapPoint (reduceZMod 313) row0_m1_localPoint) := by
  congr 1
  apply curvePoint_ext
  · exact (row0_m1_x_public).symm
  · exact (row0_m1_y_public).symm

theorem row0_V_eq :
    toGroupPoint row0_publicV =
      -(toGroupPoint (mapPoint (reduceZMod 313) row0_m4_localPoint)) := by
  have hx := row0_m4_x_public
  have hy := row0_m4_y_public
  unfold toGroupPoint
  simp only [WeierstrassCurve.Affine.Point.mk,
    WeierstrassCurve.Affine.Point.neg_some,
    WeierstrassCurve.Affine.Point.some.injEq]
  constructor
  · simpa [row0_publicV] using hx.symm
  · simp [row0_publicV, shortCurve, WeierstrassCurve.Affine.negY, hx, hy]
    norm_num <;> decide

theorem row0_public_relation :
    4 • toGroupPoint row0_publicU + toGroupPoint row0_publicV = 0 := by
  rw [row0_U_eq, row0_V_eq, row0_exact]
  simp

private noncomputable def row1_R := toGroupPoint (mapPoint (reduceZMod 421) row1_m1_localPoint)
private noncomputable def row1_U := -toGroupPoint (mapPoint (reduceZMod 421) row1_m5_localPoint)
private noncomputable def row1_V := -toGroupPoint (mapPoint (reduceZMod 421) row1_m4_localPoint)

theorem row1_chainN4 :
    RegularChainN row1_m1_localPoint 3 row1_m1_localPoint row1_m4_localPoint := by
  exact .step row1_step1 (.step row1_step2 (.step row1_step3 (.refl _)))

theorem row1_exact4 :
    toGroupPoint (mapPoint (reduceZMod 421) row1_m4_localPoint) =
      4 • row1_R := by
  exact reduced_regularChainN_from_self (reduceZMod 421) row1_chainN4

theorem row1_U_coords : pointCoords row1_U = some ((177 : ZMod 421), (399 : ZMod 421)) := by
  simp [row1_U, pointCoords_neg_toGroupPoint, row1_m5_x_public, row1_m5_y_public]
  norm_num <;> decide

theorem row1_V_coords : pointCoords row1_V = some ((49 : ZMod 421), (113 : ZMod 421)) := by
  simp [row1_V, pointCoords_neg_toGroupPoint, row1_m4_x_public, row1_m4_y_public]
  norm_num <;> decide

theorem row1_public_relation :
    (4 : ℤ) • row1_U + (-5 : ℤ) • row1_V = 0 := by
  have hU : row1_U = (-5 : ℤ) • row1_R := by
    simp [row1_U, row1_R, row1_exact] <;> rfl
  have hV : row1_V = (-4 : ℤ) • row1_R := by
    simp [row1_V, row1_R, row1_exact4] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row1_R 4 (-5)

#print axioms curvePoint_ext
#print axioms pointCoords_toGroupPoint
#print axioms pointCoords_neg_toGroupPoint
#print axioms signed_multiple_relation
#print axioms row0_U_eq
#print axioms row0_V_eq
#print axioms row0_public_relation
#print axioms row1_chainN4
#print axioms row1_exact4
#print axioms row1_U_coords
#print axioms row1_V_coords
#print axioms row1_public_relation

end XedniSignedPublicRelation
