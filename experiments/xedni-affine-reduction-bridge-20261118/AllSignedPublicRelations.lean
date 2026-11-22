import SignedPublicRelation

/-! Exact signed public-point relations for the thirteen frozen xedni lifts. -/
-- Source SHA-256: a34dd1b580483815d7f4dc61877eae9935b16873b8f9bc908b24c2e51a25154e

namespace XedniAllSignedPublicRelations

open XedniLocalZModReduction XedniRegularChainReduction
open XedniRegularGroupLaw XedniCurveEquationCertificates
open XedniRecordedRegularSteps XedniExactChainMultipliers
open XedniFiniteGroupChains XedniPublicPointReduction
open XedniSignedPublicRelation

local instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 421) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 431) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 593) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 617) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 677) := ⟨by norm_num⟩

local instance :
    (shortCurve
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) (-1)))
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) (15961)))).IsElliptic :=
  row0_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 421 ((algebraMap ℤ (localIntegers 421)) (-1)))
      (reduceZMod 421 ((algebraMap ℤ (localIntegers 421)) (9273786)))).IsElliptic :=
  row1_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 421 ((algebraMap ℤ (localIntegers 421)) (-1)))
      (reduceZMod 421 ((algebraMap ℤ (localIntegers 421)) (8839)))).IsElliptic :=
  row2_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 431 ((algebraMap ℤ (localIntegers 431)) (-1)))
      (reduceZMod 431 ((algebraMap ℤ (localIntegers 431)) (-402125)))).IsElliptic :=
  row4_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 431 ((algebraMap ℤ (localIntegers 431)) (-1)))
      (reduceZMod 431 ((algebraMap ℤ (localIntegers 431)) (367641)))).IsElliptic :=
  row5_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 593 ((algebraMap ℤ (localIntegers 593)) (-1)))
      (reduceZMod 593 ((algebraMap ℤ (localIntegers 593)) (-14513084)))).IsElliptic :=
  row6_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 593 ((algebraMap ℤ (localIntegers 593)) (-1)))
      (reduceZMod 593 ((algebraMap ℤ (localIntegers 593)) (11265)))).IsElliptic :=
  row7_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-1)))
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-43809)))).IsElliptic :=
  row8_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-1)))
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-17684456)))).IsElliptic :=
  row9_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-1)))
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-283205)))).IsElliptic :=
  row10_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 677 ((algebraMap ℤ (localIntegers 677)) (-1)))
      (reduceZMod 677 ((algebraMap ℤ (localIntegers 677)) (-3215075)))).IsElliptic :=
  row11_reduced_elliptic

/-- Row 0: the reduced starting point. -/
private noncomputable def row0_R := toGroupPoint (mapPoint (reduceZMod 313) row0_m1_localPoint)
private noncomputable def row0_U := toGroupPoint (mapPoint (reduceZMod 313) row0_m1_localPoint)
private noncomputable def row0_V := -toGroupPoint (mapPoint (reduceZMod 313) row0_m4_localPoint)

theorem row0_m1_chainN :
    RegularChainN row0_m1_localPoint 0 row0_m1_localPoint row0_m1_localPoint := by
  exact (.refl _)

theorem row0_m1_exact :
    toGroupPoint (mapPoint (reduceZMod 313) row0_m1_localPoint) = 1 • row0_R := by
  exact reduced_regularChainN_from_self (reduceZMod 313) row0_m1_chainN

theorem row0_m4_chainN :
    RegularChainN row0_m1_localPoint 3 row0_m1_localPoint row0_m4_localPoint := by
  exact (.step row0_step1 (.step row0_step2 (.step row0_step3 (.refl _))))

theorem row0_m4_exact :
    toGroupPoint (mapPoint (reduceZMod 313) row0_m4_localPoint) = 4 • row0_R := by
  exact reduced_regularChainN_from_self (reduceZMod 313) row0_m4_chainN

theorem row0_U_coords :
    pointCoords row0_U = some ((306 : ZMod 313), (125 : ZMod 313)) := by
  simp [row0_U, pointCoords_toGroupPoint, row0_m1_x_public, row0_m1_y_public] <;> (norm_num <;> decide)

theorem row0_V_coords :
    pointCoords row0_V = some ((1 : ZMod 313), (130 : ZMod 313)) := by
  simp [row0_V, pointCoords_neg_toGroupPoint, row0_m4_x_public, row0_m4_y_public] <;> (norm_num <;> decide)

theorem row0_public_relation :
    (4 : ℤ) • row0_U + (1 : ℤ) • row0_V = 0 := by
  have hU : row0_U = (1 : ℤ) • row0_R := by
    simp [row0_U, row0_R] <;> rfl
  have hV : row0_V = (-4 : ℤ) • row0_R := by
    simp [row0_V, row0_m4_exact] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row0_R 4 (1)

#print axioms row0_m1_chainN
#print axioms row0_m1_exact
#print axioms row0_m4_chainN
#print axioms row0_m4_exact
#print axioms row0_U_coords
#print axioms row0_V_coords
#print axioms row0_public_relation

/-- Row 1: the reduced starting point. -/
private noncomputable def row1_R := toGroupPoint (mapPoint (reduceZMod 421) row1_m1_localPoint)
private noncomputable def row1_U := -toGroupPoint (mapPoint (reduceZMod 421) row1_m5_localPoint)
private noncomputable def row1_V := -toGroupPoint (mapPoint (reduceZMod 421) row1_m4_localPoint)

theorem row1_m4_chainN :
    RegularChainN row1_m1_localPoint 3 row1_m1_localPoint row1_m4_localPoint := by
  exact (.step row1_step1 (.step row1_step2 (.step row1_step3 (.refl _))))

theorem row1_m4_exact :
    toGroupPoint (mapPoint (reduceZMod 421) row1_m4_localPoint) = 4 • row1_R := by
  exact reduced_regularChainN_from_self (reduceZMod 421) row1_m4_chainN

theorem row1_m5_chainN :
    RegularChainN row1_m1_localPoint 4 row1_m1_localPoint row1_m5_localPoint := by
  exact (.step row1_step1 (.step row1_step2 (.step row1_step3 (.step row1_step4 (.refl _)))))

theorem row1_m5_exact :
    toGroupPoint (mapPoint (reduceZMod 421) row1_m5_localPoint) = 5 • row1_R := by
  exact reduced_regularChainN_from_self (reduceZMod 421) row1_m5_chainN

theorem row1_U_coords :
    pointCoords row1_U = some ((177 : ZMod 421), (399 : ZMod 421)) := by
  simp [row1_U, pointCoords_neg_toGroupPoint, row1_m5_x_public, row1_m5_y_public] <;> (norm_num <;> decide)

theorem row1_V_coords :
    pointCoords row1_V = some ((49 : ZMod 421), (113 : ZMod 421)) := by
  simp [row1_V, pointCoords_neg_toGroupPoint, row1_m4_x_public, row1_m4_y_public] <;> (norm_num <;> decide)

theorem row1_public_relation :
    (4 : ℤ) • row1_U + (-5 : ℤ) • row1_V = 0 := by
  have hU : row1_U = (-5 : ℤ) • row1_R := by
    simp [row1_U, row1_m5_exact] <;> rfl
  have hV : row1_V = (-4 : ℤ) • row1_R := by
    simp [row1_V, row1_m4_exact] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row1_R 4 (-5)

#print axioms row1_m4_chainN
#print axioms row1_m4_exact
#print axioms row1_m5_chainN
#print axioms row1_m5_exact
#print axioms row1_U_coords
#print axioms row1_V_coords
#print axioms row1_public_relation

/-- Row 2: the reduced starting point. -/
private noncomputable def row2_R := toGroupPoint (mapPoint (reduceZMod 421) row2_m1_localPoint)
private noncomputable def row2_U := -toGroupPoint (mapPoint (reduceZMod 421) row2_m1_localPoint)
private noncomputable def row2_V := -toGroupPoint (mapPoint (reduceZMod 421) row2_m5_localPoint)

theorem row2_m1_chainN :
    RegularChainN row2_m1_localPoint 0 row2_m1_localPoint row2_m1_localPoint := by
  exact (.refl _)

theorem row2_m1_exact :
    toGroupPoint (mapPoint (reduceZMod 421) row2_m1_localPoint) = 1 • row2_R := by
  exact reduced_regularChainN_from_self (reduceZMod 421) row2_m1_chainN

theorem row2_m5_chainN :
    RegularChainN row2_m1_localPoint 4 row2_m1_localPoint row2_m5_localPoint := by
  exact (.step row2_step1 (.step row2_step2 (.step row2_step3 (.step row2_step4 (.refl _)))))

theorem row2_m5_exact :
    toGroupPoint (mapPoint (reduceZMod 421) row2_m5_localPoint) = 5 • row2_R := by
  exact reduced_regularChainN_from_self (reduceZMod 421) row2_m5_chainN

theorem row2_U_coords :
    pointCoords row2_U = some ((403 : ZMod 421), (366 : ZMod 421)) := by
  simp [row2_U, pointCoords_neg_toGroupPoint, row2_m1_x_public, row2_m1_y_public] <;> (norm_num <;> decide)

theorem row2_V_coords :
    pointCoords row2_V = some ((162 : ZMod 421), (384 : ZMod 421)) := by
  simp [row2_V, pointCoords_neg_toGroupPoint, row2_m5_x_public, row2_m5_y_public] <;> (norm_num <;> decide)

theorem row2_public_relation :
    (5 : ℤ) • row2_U + (-1 : ℤ) • row2_V = 0 := by
  have hU : row2_U = (-1 : ℤ) • row2_R := by
    simp [row2_U, row2_R] <;> rfl
  have hV : row2_V = (-5 : ℤ) • row2_R := by
    simp [row2_V, row2_m5_exact] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row2_R 5 (-1)

#print axioms row2_m1_chainN
#print axioms row2_m1_exact
#print axioms row2_m5_chainN
#print axioms row2_m5_exact
#print axioms row2_U_coords
#print axioms row2_V_coords
#print axioms row2_public_relation

/-- Row 3: the reduced starting point. -/
private noncomputable def row3_R := toGroupPoint (mapPoint (reduceZMod 421) row3_m1_localPoint)
private noncomputable def row3_U := toGroupPoint (mapPoint (reduceZMod 421) row3_m3_localPoint)
private noncomputable def row3_V := -toGroupPoint (mapPoint (reduceZMod 421) row3_m5_localPoint)

theorem row3_m3_chainN :
    RegularChainN row3_m1_localPoint 2 row3_m1_localPoint row3_m3_localPoint := by
  exact (.step row3_step1 (.step row3_step2 (.refl _)))

theorem row3_m3_exact :
    toGroupPoint (mapPoint (reduceZMod 421) row3_m3_localPoint) = 3 • row3_R := by
  exact reduced_regularChainN_from_self (reduceZMod 421) row3_m3_chainN

theorem row3_m5_chainN :
    RegularChainN row3_m1_localPoint 4 row3_m1_localPoint row3_m5_localPoint := by
  exact (.step row3_step1 (.step row3_step2 (.step row3_step3 (.step row3_step4 (.refl _)))))

theorem row3_m5_exact :
    toGroupPoint (mapPoint (reduceZMod 421) row3_m5_localPoint) = 5 • row3_R := by
  exact reduced_regularChainN_from_self (reduceZMod 421) row3_m5_chainN

theorem row3_U_coords :
    pointCoords row3_U = some ((203 : ZMod 421), (164 : ZMod 421)) := by
  simp [row3_U, pointCoords_toGroupPoint, row3_m3_x_public, row3_m3_y_public] <;> (norm_num <;> decide)

theorem row3_V_coords :
    pointCoords row3_V = some ((162 : ZMod 421), (384 : ZMod 421)) := by
  simp [row3_V, pointCoords_neg_toGroupPoint, row3_m5_x_public, row3_m5_y_public] <;> (norm_num <;> decide)

theorem row3_public_relation :
    (5 : ℤ) • row3_U + (3 : ℤ) • row3_V = 0 := by
  have hU : row3_U = (3 : ℤ) • row3_R := by
    simp [row3_U, row3_m3_exact] <;> rfl
  have hV : row3_V = (-5 : ℤ) • row3_R := by
    simp [row3_V, row3_m5_exact] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row3_R 5 (3)

#print axioms row3_m3_chainN
#print axioms row3_m3_exact
#print axioms row3_m5_chainN
#print axioms row3_m5_exact
#print axioms row3_U_coords
#print axioms row3_V_coords
#print axioms row3_public_relation

/-- Row 4: the reduced starting point. -/
private noncomputable def row4_R := toGroupPoint (mapPoint (reduceZMod 431) row4_m1_localPoint)
private noncomputable def row4_U := toGroupPoint (mapPoint (reduceZMod 431) row4_m5_localPoint)
private noncomputable def row4_V := -toGroupPoint (mapPoint (reduceZMod 431) row4_m6_localPoint)

theorem row4_m5_chainN :
    RegularChainN row4_m1_localPoint 4 row4_m1_localPoint row4_m5_localPoint := by
  exact (.step row4_step1 (.step row4_step2 (.step row4_step3 (.step row4_step4 (.refl _)))))

theorem row4_m5_exact :
    toGroupPoint (mapPoint (reduceZMod 431) row4_m5_localPoint) = 5 • row4_R := by
  exact reduced_regularChainN_from_self (reduceZMod 431) row4_m5_chainN

theorem row4_m6_chainN :
    RegularChainN row4_m1_localPoint 5 row4_m1_localPoint row4_m6_localPoint := by
  exact (.step row4_step1 (.step row4_step2 (.step row4_step3 (.step row4_step4 (.step row4_step5 (.refl _))))))

theorem row4_m6_exact :
    toGroupPoint (mapPoint (reduceZMod 431) row4_m6_localPoint) = 6 • row4_R := by
  exact reduced_regularChainN_from_self (reduceZMod 431) row4_m6_chainN

theorem row4_U_coords :
    pointCoords row4_U = some ((303 : ZMod 431), (282 : ZMod 431)) := by
  simp [row4_U, pointCoords_toGroupPoint, row4_m5_x_public, row4_m5_y_public] <;> (norm_num <;> decide)

theorem row4_V_coords :
    pointCoords row4_V = some ((144 : ZMod 431), (386 : ZMod 431)) := by
  simp [row4_V, pointCoords_neg_toGroupPoint, row4_m6_x_public, row4_m6_y_public] <;> (norm_num <;> decide)

theorem row4_public_relation :
    (6 : ℤ) • row4_U + (5 : ℤ) • row4_V = 0 := by
  have hU : row4_U = (5 : ℤ) • row4_R := by
    simp [row4_U, row4_m5_exact] <;> rfl
  have hV : row4_V = (-6 : ℤ) • row4_R := by
    simp [row4_V, row4_m6_exact] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row4_R 6 (5)

#print axioms row4_m5_chainN
#print axioms row4_m5_exact
#print axioms row4_m6_chainN
#print axioms row4_m6_exact
#print axioms row4_U_coords
#print axioms row4_V_coords
#print axioms row4_public_relation

/-- Row 5: the reduced starting point. -/
private noncomputable def row5_R := toGroupPoint (mapPoint (reduceZMod 431) row5_m1_localPoint)
private noncomputable def row5_U := toGroupPoint (mapPoint (reduceZMod 431) row5_m5_localPoint)
private noncomputable def row5_V := -toGroupPoint (mapPoint (reduceZMod 431) row5_m1_localPoint)

theorem row5_m1_chainN :
    RegularChainN row5_m1_localPoint 0 row5_m1_localPoint row5_m1_localPoint := by
  exact (.refl _)

theorem row5_m1_exact :
    toGroupPoint (mapPoint (reduceZMod 431) row5_m1_localPoint) = 1 • row5_R := by
  exact reduced_regularChainN_from_self (reduceZMod 431) row5_m1_chainN

theorem row5_m5_chainN :
    RegularChainN row5_m1_localPoint 4 row5_m1_localPoint row5_m5_localPoint := by
  exact (.step row5_step1 (.step row5_step2 (.step row5_step3 (.step row5_step4 (.refl _)))))

theorem row5_m5_exact :
    toGroupPoint (mapPoint (reduceZMod 431) row5_m5_localPoint) = 5 • row5_R := by
  exact reduced_regularChainN_from_self (reduceZMod 431) row5_m5_chainN

theorem row5_U_coords :
    pointCoords row5_U = some ((376 : ZMod 431), (123 : ZMod 431)) := by
  simp [row5_U, pointCoords_toGroupPoint, row5_m5_x_public, row5_m5_y_public] <;> (norm_num <;> decide)

theorem row5_V_coords :
    pointCoords row5_V = some ((360 : ZMod 431), (99 : ZMod 431)) := by
  simp [row5_V, pointCoords_neg_toGroupPoint, row5_m1_x_public, row5_m1_y_public] <;> (norm_num <;> decide)

theorem row5_public_relation :
    (1 : ℤ) • row5_U + (5 : ℤ) • row5_V = 0 := by
  have hU : row5_U = (5 : ℤ) • row5_R := by
    simp [row5_U, row5_m5_exact] <;> rfl
  have hV : row5_V = (-1 : ℤ) • row5_R := by
    simp [row5_V, row5_R] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row5_R 1 (5)

#print axioms row5_m1_chainN
#print axioms row5_m1_exact
#print axioms row5_m5_chainN
#print axioms row5_m5_exact
#print axioms row5_U_coords
#print axioms row5_V_coords
#print axioms row5_public_relation

/-- Row 6: the reduced starting point. -/
private noncomputable def row6_R := toGroupPoint (mapPoint (reduceZMod 593) row6_m1_localPoint)
private noncomputable def row6_U := -toGroupPoint (mapPoint (reduceZMod 593) row6_m1_localPoint)
private noncomputable def row6_V := -toGroupPoint (mapPoint (reduceZMod 593) row6_m4_localPoint)

theorem row6_m1_chainN :
    RegularChainN row6_m1_localPoint 0 row6_m1_localPoint row6_m1_localPoint := by
  exact (.refl _)

theorem row6_m1_exact :
    toGroupPoint (mapPoint (reduceZMod 593) row6_m1_localPoint) = 1 • row6_R := by
  exact reduced_regularChainN_from_self (reduceZMod 593) row6_m1_chainN

theorem row6_m4_chainN :
    RegularChainN row6_m1_localPoint 3 row6_m1_localPoint row6_m4_localPoint := by
  exact (.step row6_step1 (.step row6_step2 (.step row6_step3 (.refl _))))

theorem row6_m4_exact :
    toGroupPoint (mapPoint (reduceZMod 593) row6_m4_localPoint) = 4 • row6_R := by
  exact reduced_regularChainN_from_self (reduceZMod 593) row6_m4_chainN

theorem row6_U_coords :
    pointCoords row6_U = some ((244 : ZMod 593), (477 : ZMod 593)) := by
  simp [row6_U, pointCoords_neg_toGroupPoint, row6_m1_x_public, row6_m1_y_public] <;> (norm_num <;> decide)

theorem row6_V_coords :
    pointCoords row6_V = some ((435 : ZMod 593), (202 : ZMod 593)) := by
  simp [row6_V, pointCoords_neg_toGroupPoint, row6_m4_x_public, row6_m4_y_public] <;> (norm_num <;> decide)

theorem row6_public_relation :
    (4 : ℤ) • row6_U + (-1 : ℤ) • row6_V = 0 := by
  have hU : row6_U = (-1 : ℤ) • row6_R := by
    simp [row6_U, row6_R] <;> rfl
  have hV : row6_V = (-4 : ℤ) • row6_R := by
    simp [row6_V, row6_m4_exact] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row6_R 4 (-1)

#print axioms row6_m1_chainN
#print axioms row6_m1_exact
#print axioms row6_m4_chainN
#print axioms row6_m4_exact
#print axioms row6_U_coords
#print axioms row6_V_coords
#print axioms row6_public_relation

/-- Row 7: the reduced starting point. -/
private noncomputable def row7_R := toGroupPoint (mapPoint (reduceZMod 593) row7_m1_localPoint)
private noncomputable def row7_U := toGroupPoint (mapPoint (reduceZMod 593) row7_m5_localPoint)
private noncomputable def row7_V := -toGroupPoint (mapPoint (reduceZMod 593) row7_m1_localPoint)

theorem row7_m1_chainN :
    RegularChainN row7_m1_localPoint 0 row7_m1_localPoint row7_m1_localPoint := by
  exact (.refl _)

theorem row7_m1_exact :
    toGroupPoint (mapPoint (reduceZMod 593) row7_m1_localPoint) = 1 • row7_R := by
  exact reduced_regularChainN_from_self (reduceZMod 593) row7_m1_chainN

theorem row7_m5_chainN :
    RegularChainN row7_m1_localPoint 4 row7_m1_localPoint row7_m5_localPoint := by
  exact (.step row7_step1 (.step row7_step2 (.step row7_step3 (.step row7_step4 (.refl _)))))

theorem row7_m5_exact :
    toGroupPoint (mapPoint (reduceZMod 593) row7_m5_localPoint) = 5 • row7_R := by
  exact reduced_regularChainN_from_self (reduceZMod 593) row7_m5_chainN

theorem row7_U_coords :
    pointCoords row7_U = some ((92 : ZMod 593), (551 : ZMod 593)) := by
  simp [row7_U, pointCoords_toGroupPoint, row7_m5_x_public, row7_m5_y_public] <;> (norm_num <;> decide)

theorem row7_V_coords :
    pointCoords row7_V = some ((572 : ZMod 593), (548 : ZMod 593)) := by
  simp [row7_V, pointCoords_neg_toGroupPoint, row7_m1_x_public, row7_m1_y_public] <;> (norm_num <;> decide)

theorem row7_public_relation :
    (1 : ℤ) • row7_U + (5 : ℤ) • row7_V = 0 := by
  have hU : row7_U = (5 : ℤ) • row7_R := by
    simp [row7_U, row7_m5_exact] <;> rfl
  have hV : row7_V = (-1 : ℤ) • row7_R := by
    simp [row7_V, row7_R] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row7_R 1 (5)

#print axioms row7_m1_chainN
#print axioms row7_m1_exact
#print axioms row7_m5_chainN
#print axioms row7_m5_exact
#print axioms row7_U_coords
#print axioms row7_V_coords
#print axioms row7_public_relation

/-- Row 8: the reduced starting point. -/
private noncomputable def row8_R := toGroupPoint (mapPoint (reduceZMod 617) row8_m1_localPoint)
private noncomputable def row8_U := -toGroupPoint (mapPoint (reduceZMod 617) row8_m6_localPoint)
private noncomputable def row8_V := -toGroupPoint (mapPoint (reduceZMod 617) row8_m1_localPoint)

theorem row8_m1_chainN :
    RegularChainN row8_m1_localPoint 0 row8_m1_localPoint row8_m1_localPoint := by
  exact (.refl _)

theorem row8_m1_exact :
    toGroupPoint (mapPoint (reduceZMod 617) row8_m1_localPoint) = 1 • row8_R := by
  exact reduced_regularChainN_from_self (reduceZMod 617) row8_m1_chainN

theorem row8_m6_chainN :
    RegularChainN row8_m1_localPoint 5 row8_m1_localPoint row8_m6_localPoint := by
  exact (.step row8_step1 (.step row8_step2 (.step row8_step3 (.step row8_step4 (.step row8_step5 (.refl _))))))

theorem row8_m6_exact :
    toGroupPoint (mapPoint (reduceZMod 617) row8_m6_localPoint) = 6 • row8_R := by
  exact reduced_regularChainN_from_self (reduceZMod 617) row8_m6_chainN

theorem row8_U_coords :
    pointCoords row8_U = some ((378 : ZMod 617), (436 : ZMod 617)) := by
  simp [row8_U, pointCoords_neg_toGroupPoint, row8_m6_x_public, row8_m6_y_public] <;> (norm_num <;> decide)

theorem row8_V_coords :
    pointCoords row8_V = some ((38 : ZMod 617), (105 : ZMod 617)) := by
  simp [row8_V, pointCoords_neg_toGroupPoint, row8_m1_x_public, row8_m1_y_public] <;> (norm_num <;> decide)

theorem row8_public_relation :
    (1 : ℤ) • row8_U + (-6 : ℤ) • row8_V = 0 := by
  have hU : row8_U = (-6 : ℤ) • row8_R := by
    simp [row8_U, row8_m6_exact] <;> rfl
  have hV : row8_V = (-1 : ℤ) • row8_R := by
    simp [row8_V, row8_R] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row8_R 1 (-6)

#print axioms row8_m1_chainN
#print axioms row8_m1_exact
#print axioms row8_m6_chainN
#print axioms row8_m6_exact
#print axioms row8_U_coords
#print axioms row8_V_coords
#print axioms row8_public_relation

/-- Row 9: the reduced starting point. -/
private noncomputable def row9_R := toGroupPoint (mapPoint (reduceZMod 617) row9_m1_localPoint)
private noncomputable def row9_U := toGroupPoint (mapPoint (reduceZMod 617) row9_m3_localPoint)
private noncomputable def row9_V := -toGroupPoint (mapPoint (reduceZMod 617) row9_m5_localPoint)

theorem row9_m3_chainN :
    RegularChainN row9_m1_localPoint 2 row9_m1_localPoint row9_m3_localPoint := by
  exact (.step row9_step1 (.step row9_step2 (.refl _)))

theorem row9_m3_exact :
    toGroupPoint (mapPoint (reduceZMod 617) row9_m3_localPoint) = 3 • row9_R := by
  exact reduced_regularChainN_from_self (reduceZMod 617) row9_m3_chainN

theorem row9_m5_chainN :
    RegularChainN row9_m1_localPoint 4 row9_m1_localPoint row9_m5_localPoint := by
  exact (.step row9_step1 (.step row9_step2 (.step row9_step3 (.step row9_step4 (.refl _)))))

theorem row9_m5_exact :
    toGroupPoint (mapPoint (reduceZMod 617) row9_m5_localPoint) = 5 • row9_R := by
  exact reduced_regularChainN_from_self (reduceZMod 617) row9_m5_chainN

theorem row9_U_coords :
    pointCoords row9_U = some ((327 : ZMod 617), (609 : ZMod 617)) := by
  simp [row9_U, pointCoords_toGroupPoint, row9_m3_x_public, row9_m3_y_public] <;> (norm_num <;> decide)

theorem row9_V_coords :
    pointCoords row9_V = some ((542 : ZMod 617), (328 : ZMod 617)) := by
  simp [row9_V, pointCoords_neg_toGroupPoint, row9_m5_x_public, row9_m5_y_public] <;> (norm_num <;> decide)

theorem row9_public_relation :
    (5 : ℤ) • row9_U + (3 : ℤ) • row9_V = 0 := by
  have hU : row9_U = (3 : ℤ) • row9_R := by
    simp [row9_U, row9_m3_exact] <;> rfl
  have hV : row9_V = (-5 : ℤ) • row9_R := by
    simp [row9_V, row9_m5_exact] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row9_R 5 (3)

#print axioms row9_m3_chainN
#print axioms row9_m3_exact
#print axioms row9_m5_chainN
#print axioms row9_m5_exact
#print axioms row9_U_coords
#print axioms row9_V_coords
#print axioms row9_public_relation

/-- Row 10: the reduced starting point. -/
private noncomputable def row10_R := toGroupPoint (mapPoint (reduceZMod 617) row10_m1_localPoint)
private noncomputable def row10_U := toGroupPoint (mapPoint (reduceZMod 617) row10_m4_localPoint)
private noncomputable def row10_V := -toGroupPoint (mapPoint (reduceZMod 617) row10_m5_localPoint)

theorem row10_m4_chainN :
    RegularChainN row10_m1_localPoint 3 row10_m1_localPoint row10_m4_localPoint := by
  exact (.step row10_step1 (.step row10_step2 (.step row10_step3 (.refl _))))

theorem row10_m4_exact :
    toGroupPoint (mapPoint (reduceZMod 617) row10_m4_localPoint) = 4 • row10_R := by
  exact reduced_regularChainN_from_self (reduceZMod 617) row10_m4_chainN

theorem row10_m5_chainN :
    RegularChainN row10_m1_localPoint 4 row10_m1_localPoint row10_m5_localPoint := by
  exact (.step row10_step1 (.step row10_step2 (.step row10_step3 (.step row10_step4 (.refl _)))))

theorem row10_m5_exact :
    toGroupPoint (mapPoint (reduceZMod 617) row10_m5_localPoint) = 5 • row10_R := by
  exact reduced_regularChainN_from_self (reduceZMod 617) row10_m5_chainN

theorem row10_U_coords :
    pointCoords row10_U = some ((590 : ZMod 617), (324 : ZMod 617)) := by
  simp [row10_U, pointCoords_toGroupPoint, row10_m4_x_public, row10_m4_y_public] <;> (norm_num <;> decide)

theorem row10_V_coords :
    pointCoords row10_V = some ((338 : ZMod 617), (369 : ZMod 617)) := by
  simp [row10_V, pointCoords_neg_toGroupPoint, row10_m5_x_public, row10_m5_y_public] <;> (norm_num <;> decide)

theorem row10_public_relation :
    (5 : ℤ) • row10_U + (4 : ℤ) • row10_V = 0 := by
  have hU : row10_U = (4 : ℤ) • row10_R := by
    simp [row10_U, row10_m4_exact] <;> rfl
  have hV : row10_V = (-5 : ℤ) • row10_R := by
    simp [row10_V, row10_m5_exact] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row10_R 5 (4)

#print axioms row10_m4_chainN
#print axioms row10_m4_exact
#print axioms row10_m5_chainN
#print axioms row10_m5_exact
#print axioms row10_U_coords
#print axioms row10_V_coords
#print axioms row10_public_relation

/-- Row 11: the reduced starting point. -/
private noncomputable def row11_R := toGroupPoint (mapPoint (reduceZMod 677) row11_m1_localPoint)
private noncomputable def row11_U := -toGroupPoint (mapPoint (reduceZMod 677) row11_m6_localPoint)
private noncomputable def row11_V := -toGroupPoint (mapPoint (reduceZMod 677) row11_m1_localPoint)

theorem row11_m1_chainN :
    RegularChainN row11_m1_localPoint 0 row11_m1_localPoint row11_m1_localPoint := by
  exact (.refl _)

theorem row11_m1_exact :
    toGroupPoint (mapPoint (reduceZMod 677) row11_m1_localPoint) = 1 • row11_R := by
  exact reduced_regularChainN_from_self (reduceZMod 677) row11_m1_chainN

theorem row11_m6_chainN :
    RegularChainN row11_m1_localPoint 5 row11_m1_localPoint row11_m6_localPoint := by
  exact (.step row11_step1 (.step row11_step2 (.step row11_step3 (.step row11_step4 (.step row11_step5 (.refl _))))))

theorem row11_m6_exact :
    toGroupPoint (mapPoint (reduceZMod 677) row11_m6_localPoint) = 6 • row11_R := by
  exact reduced_regularChainN_from_self (reduceZMod 677) row11_m6_chainN

theorem row11_U_coords :
    pointCoords row11_U = some ((541 : ZMod 677), (635 : ZMod 677)) := by
  simp [row11_U, pointCoords_neg_toGroupPoint, row11_m6_x_public, row11_m6_y_public] <;> (norm_num <;> decide)

theorem row11_V_coords :
    pointCoords row11_V = some ((148 : ZMod 677), (514 : ZMod 677)) := by
  simp [row11_V, pointCoords_neg_toGroupPoint, row11_m1_x_public, row11_m1_y_public] <;> (norm_num <;> decide)

theorem row11_public_relation :
    (1 : ℤ) • row11_U + (-6 : ℤ) • row11_V = 0 := by
  have hU : row11_U = (-6 : ℤ) • row11_R := by
    simp [row11_U, row11_m6_exact] <;> rfl
  have hV : row11_V = (-1 : ℤ) • row11_R := by
    simp [row11_V, row11_R] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row11_R 1 (-6)

#print axioms row11_m1_chainN
#print axioms row11_m1_exact
#print axioms row11_m6_chainN
#print axioms row11_m6_exact
#print axioms row11_U_coords
#print axioms row11_V_coords
#print axioms row11_public_relation

/-- Row 12: the reduced starting point. -/
private noncomputable def row12_R := toGroupPoint (mapPoint (reduceZMod 677) row12_m1_localPoint)
private noncomputable def row12_U := -toGroupPoint (mapPoint (reduceZMod 677) row12_m1_localPoint)
private noncomputable def row12_V := -toGroupPoint (mapPoint (reduceZMod 677) row12_m6_localPoint)

theorem row12_m1_chainN :
    RegularChainN row12_m1_localPoint 0 row12_m1_localPoint row12_m1_localPoint := by
  exact (.refl _)

theorem row12_m1_exact :
    toGroupPoint (mapPoint (reduceZMod 677) row12_m1_localPoint) = 1 • row12_R := by
  exact reduced_regularChainN_from_self (reduceZMod 677) row12_m1_chainN

theorem row12_m6_chainN :
    RegularChainN row12_m1_localPoint 5 row12_m1_localPoint row12_m6_localPoint := by
  exact (.step row12_step1 (.step row12_step2 (.step row12_step3 (.step row12_step4 (.step row12_step5 (.refl _))))))

theorem row12_m6_exact :
    toGroupPoint (mapPoint (reduceZMod 677) row12_m6_localPoint) = 6 • row12_R := by
  exact reduced_regularChainN_from_self (reduceZMod 677) row12_m6_chainN

theorem row12_U_coords :
    pointCoords row12_U = some ((148 : ZMod 677), (514 : ZMod 677)) := by
  simp [row12_U, pointCoords_neg_toGroupPoint, row12_m1_x_public, row12_m1_y_public] <;> (norm_num <;> decide)

theorem row12_V_coords :
    pointCoords row12_V = some ((541 : ZMod 677), (635 : ZMod 677)) := by
  simp [row12_V, pointCoords_neg_toGroupPoint, row12_m6_x_public, row12_m6_y_public] <;> (norm_num <;> decide)

theorem row12_public_relation :
    (6 : ℤ) • row12_U + (-1 : ℤ) • row12_V = 0 := by
  have hU : row12_U = (-1 : ℤ) • row12_R := by
    simp [row12_U, row12_R] <;> rfl
  have hV : row12_V = (-6 : ℤ) • row12_R := by
    simp [row12_V, row12_m6_exact] <;> rfl
  rw [hU, hV]
  exact signed_multiple_relation row12_R 6 (-1)

#print axioms row12_m1_chainN
#print axioms row12_m1_exact
#print axioms row12_m6_chainN
#print axioms row12_m6_exact
#print axioms row12_U_coords
#print axioms row12_V_coords
#print axioms row12_public_relation

end XedniAllSignedPublicRelations
