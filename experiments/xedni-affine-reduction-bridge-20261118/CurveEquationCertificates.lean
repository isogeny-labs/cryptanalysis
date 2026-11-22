import RationalCurveBridge
import CoordinateCertificates
import Mathlib.Tactic

/-!
Rational curve equations and prime-local curve points for every point on
the thirteen recorded addition paths. Generated from source SHA-256
`a34dd1b580483815d7f4dc61877eae9935b16873b8f9bc908b24c2e51a25154e` by `generate_curve_equation_certificates.py`.
-/

namespace XedniCurveEquationCertificates

open XedniLocalZModReduction XedniRationalLocalWitness
open XedniRationalCurveBridge XedniRegularChainReduction
open XedniCoordinateCertificates

local instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 421) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 431) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 593) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 617) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 677) := ⟨by norm_num⟩

/-- Row 0, rational curve equation for 1T. -/
theorem row0_m1_curve :
    ((125 : ℚ) / (1 : ℚ)) ^ 2 =
      ((-7 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((-7 : ℚ) / (1 : ℚ)) + (15961 : ℚ) := by
  norm_num

/-- Row 0, prime-local curve point 1T. -/
noncomputable def row0_m1_localPoint :
    CurvePoint (localIntegers 313)
      ((algebraMap ℤ (localIntegers 313)) (-1))
      ((algebraMap ℤ (localIntegers 313)) (15961)) :=
  localCurvePoint 313 (-1) (15961)
    ((-7 : ℚ) / (1 : ℚ)) ((125 : ℚ) / (1 : ℚ))
    row0_m1_x row0_m1_y row0_m1_curve

#print axioms row0_m1_curve
#print axioms row0_m1_localPoint

/-- Row 0, rational curve equation for 2T. -/
theorem row0_m2_curve :
    ((-268482767 : ℚ) / (1953125 : ℚ)) ^ 2 =
      ((224079 : ℚ) / (15625 : ℚ)) ^ 3 + (-1 : ℚ) * ((224079 : ℚ) / (15625 : ℚ)) + (15961 : ℚ) := by
  norm_num

/-- Row 0, prime-local curve point 2T. -/
noncomputable def row0_m2_localPoint :
    CurvePoint (localIntegers 313)
      ((algebraMap ℤ (localIntegers 313)) (-1))
      ((algebraMap ℤ (localIntegers 313)) (15961)) :=
  localCurvePoint 313 (-1) (15961)
    ((224079 : ℚ) / (15625 : ℚ)) ((-268482767 : ℚ) / (1953125 : ℚ))
    row0_m2_x row0_m2_y row0_m2_curve

#print axioms row0_m2_curve
#print axioms row0_m2_localPoint

/-- Row 0, rational curve equation for 3T. -/
theorem row0_m3_curve :
    ((8022576766107531125 : ℚ) / (4634659227682583 : ℚ)) ^ 2 =
      ((4000457986672 : ℚ) / (27797892529 : ℚ)) ^ 3 + (-1 : ℚ) * ((4000457986672 : ℚ) / (27797892529 : ℚ)) + (15961 : ℚ) := by
  norm_num

/-- Row 0, prime-local curve point 3T. -/
noncomputable def row0_m3_localPoint :
    CurvePoint (localIntegers 313)
      ((algebraMap ℤ (localIntegers 313)) (-1))
      ((algebraMap ℤ (localIntegers 313)) (15961)) :=
  localCurvePoint 313 (-1) (15961)
    ((4000457986672 : ℚ) / (27797892529 : ℚ)) ((8022576766107531125 : ℚ) / (4634659227682583 : ℚ))
    row0_m3_x row0_m3_y row0_m3_curve

#print axioms row0_m3_curve
#print axioms row0_m3_localPoint

/-- Row 0, rational curve equation for 4T. -/
theorem row0_m4_curve :
    ((1977418304204033859577942351663013 : ℚ) / (37798910677688541009983716796875 : ℚ)) ^ 2 =
      ((-26650279307333340077261 : ℚ) / (1126296815249629515625 : ℚ)) ^ 3 + (-1 : ℚ) * ((-26650279307333340077261 : ℚ) / (1126296815249629515625 : ℚ)) + (15961 : ℚ) := by
  norm_num

/-- Row 0, prime-local curve point 4T. -/
noncomputable def row0_m4_localPoint :
    CurvePoint (localIntegers 313)
      ((algebraMap ℤ (localIntegers 313)) (-1))
      ((algebraMap ℤ (localIntegers 313)) (15961)) :=
  localCurvePoint 313 (-1) (15961)
    ((-26650279307333340077261 : ℚ) / (1126296815249629515625 : ℚ)) ((1977418304204033859577942351663013 : ℚ) / (37798910677688541009983716796875 : ℚ))
    row0_m4_x row0_m4_y row0_m4_curve

#print axioms row0_m4_curve
#print axioms row0_m4_localPoint

/-- Row 1, rational curve equation for 1T. -/
theorem row1_m1_curve :
    ((114 : ℚ) / (1 : ℚ)) ^ 2 =
      ((-210 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((-210 : ℚ) / (1 : ℚ)) + (9273786 : ℚ) := by
  norm_num

/-- Row 1, prime-local curve point 1T. -/
noncomputable def row1_m1_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (9273786)) :=
  localCurvePoint 421 (-1) (9273786)
    ((-210 : ℚ) / (1 : ℚ)) ((114 : ℚ) / (1 : ℚ))
    row1_m1_x row1_m1_y row1_m1_curve

#print axioms row1_m1_curve
#print axioms row1_m1_localPoint

/-- Row 1, rational curve equation for 2T. -/
theorem row1_m2_curve :
    ((-2319966890361107 : ℚ) / (11852352 : ℚ)) ^ 2 =
      ((17524858681 : ℚ) / (51984 : ℚ)) ^ 3 + (-1 : ℚ) * ((17524858681 : ℚ) / (51984 : ℚ)) + (9273786 : ℚ) := by
  norm_num

/-- Row 1, prime-local curve point 2T. -/
noncomputable def row1_m2_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (9273786)) :=
  localCurvePoint 421 (-1) (9273786)
    ((17524858681 : ℚ) / (51984 : ℚ)) ((-2319966890361107 : ℚ) / (11852352 : ℚ))
    row1_m2_x row1_m2_y row1_m2_curve

#print axioms row1_m2_curve
#print axioms row1_m2_localPoint

/-- Row 1, rational curve equation for 3T. -/
theorem row1_m3_curve :
    ((1839582342262411021362145335461766 : ℚ) / (5392310815320252901238283401161 : ℚ)) ^ 2 =
      ((-64334515065147393566034 : ℚ) / (307503416108592653041 : ℚ)) ^ 3 + (-1 : ℚ) * ((-64334515065147393566034 : ℚ) / (307503416108592653041 : ℚ)) + (9273786 : ℚ) := by
  norm_num

/-- Row 1, prime-local curve point 3T. -/
noncomputable def row1_m3_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (9273786)) :=
  localCurvePoint 421 (-1) (9273786)
    ((-64334515065147393566034 : ℚ) / (307503416108592653041 : ℚ)) ((1839582342262411021362145335461766 : ℚ) / (5392310815320252901238283401161 : ℚ))
    row1_m3_x row1_m3_y row1_m3_curve

#print axioms row1_m3_curve
#print axioms row1_m3_localPoint

/-- Row 1, rational curve equation for 4T. -/
theorem row1_m4_curve :
    ((-28968576138357017202042244440043053790221957208391810185307665 : ℚ) / (1183967792886266316779962539649724586898400986070681088 : ℚ)) ^ 2 =
      ((94323106859153273434564086544158054420577 : ℚ) / (1119162781685499416647242528284403264 : ℚ)) ^ 3 + (-1 : ℚ) * ((94323106859153273434564086544158054420577 : ℚ) / (1119162781685499416647242528284403264 : ℚ)) + (9273786 : ℚ) := by
  norm_num

/-- Row 1, prime-local curve point 4T. -/
noncomputable def row1_m4_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (9273786)) :=
  localCurvePoint 421 (-1) (9273786)
    ((94323106859153273434564086544158054420577 : ℚ) / (1119162781685499416647242528284403264 : ℚ)) ((-28968576138357017202042244440043053790221957208391810185307665 : ℚ) / (1183967792886266316779962539649724586898400986070681088 : ℚ))
    row1_m4_x row1_m4_y row1_m4_curve

#print axioms row1_m4_curve
#print axioms row1_m4_localPoint

/-- Row 1, rational curve equation for 5T. -/
theorem row1_m5_curve :
    ((88706460511322288237480609867404970395792531213416032466242832798579163925728238955386128233642 : ℚ) / (156791213713274487384947970675768732930766209404878727572455822047852757664006201919811652633 : ℚ)) ^ 2 =
      ((-6037892091791484835810617682772208834049779090336529551651651666 : ℚ) / (29076880704459317355937847032965558435335406229818019164082129 : ℚ)) ^ 3 + (-1 : ℚ) * ((-6037892091791484835810617682772208834049779090336529551651651666 : ℚ) / (29076880704459317355937847032965558435335406229818019164082129 : ℚ)) + (9273786 : ℚ) := by
  norm_num

/-- Row 1, prime-local curve point 5T. -/
noncomputable def row1_m5_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (9273786)) :=
  localCurvePoint 421 (-1) (9273786)
    ((-6037892091791484835810617682772208834049779090336529551651651666 : ℚ) / (29076880704459317355937847032965558435335406229818019164082129 : ℚ)) ((88706460511322288237480609867404970395792531213416032466242832798579163925728238955386128233642 : ℚ) / (156791213713274487384947970675768732930766209404878727572455822047852757664006201919811652633 : ℚ))
    row1_m5_x row1_m5_y row1_m5_curve

#print axioms row1_m5_curve
#print axioms row1_m5_localPoint

/-- Row 2, rational curve equation for 1T. -/
theorem row2_m1_curve :
    ((55 : ℚ) / (1 : ℚ)) ^ 2 =
      ((-18 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((-18 : ℚ) / (1 : ℚ)) + (8839 : ℚ) := by
  norm_num

/-- Row 2, prime-local curve point 1T. -/
noncomputable def row2_m1_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (8839)) :=
  localCurvePoint 421 (-1) (8839)
    ((-18 : ℚ) / (1 : ℚ)) ((55 : ℚ) / (1 : ℚ))
    row2_m1_x row2_m1_y row2_m1_curve

#print axioms row2_m1_curve
#print axioms row2_m1_localPoint

/-- Row 2, rational curve equation for 2T. -/
theorem row2_m2_curve :
    ((-1623155011 : ℚ) / (1331000 : ℚ)) ^ 2 =
      ((1378441 : ℚ) / (12100 : ℚ)) ^ 3 + (-1 : ℚ) * ((1378441 : ℚ) / (12100 : ℚ)) + (8839 : ℚ) := by
  norm_num

/-- Row 2, prime-local curve point 2T. -/
noncomputable def row2_m2_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (8839)) :=
  localCurvePoint 421 (-1) (8839)
    ((1378441 : ℚ) / (12100 : ℚ)) ((-1623155011 : ℚ) / (1331000 : ℚ))
    row2_m2_x row2_m2_y row2_m2_curve

#print axioms row2_m2_curve
#print axioms row2_m2_localPoint

/-- Row 2, rational curve equation for 3T. -/
theorem row2_m3_curve :
    ((382064229689165922965 : ℚ) / (4067198651273825521 : ℚ)) ^ 2 =
      ((-6583384675258 : ℚ) / (2547985330081 : ℚ)) ^ 3 + (-1 : ℚ) * ((-6583384675258 : ℚ) / (2547985330081 : ℚ)) + (8839 : ℚ) := by
  norm_num

/-- Row 2, prime-local curve point 3T. -/
noncomputable def row2_m3_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (8839)) :=
  localCurvePoint 421 (-1) (8839)
    ((-6583384675258 : ℚ) / (2547985330081 : ℚ)) ((382064229689165922965 : ℚ) / (4067198651273825521 : ℚ))
    row2_m3_x row2_m3_y row2_m3_curve

#print axioms row2_m3_curve
#print axioms row2_m3_localPoint

/-- Row 2, rational curve equation for 4T. -/
theorem row2_m4_curve :
    ((-7675750746049392913879186847997204641 : ℚ) / (45535282262802338704778275892488000 : ℚ)) ^ 2 =
      ((3438256701666689140231361 : ℚ) / (127516197983145449856400 : ℚ)) ^ 3 + (-1 : ℚ) * ((3438256701666689140231361 : ℚ) / (127516197983145449856400 : ℚ)) + (8839 : ℚ) := by
  norm_num

/-- Row 2, prime-local curve point 4T. -/
noncomputable def row2_m4_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (8839)) :=
  localCurvePoint 421 (-1) (8839)
    ((3438256701666689140231361 : ℚ) / (127516197983145449856400 : ℚ)) ((-7675750746049392913879186847997204641 : ℚ) / (45535282262802338704778275892488000 : ℚ))
    row2_m4_x row2_m4_y row2_m4_curve

#print axioms row2_m4_curve
#print axioms row2_m4_localPoint

/-- Row 2, rational curve equation for 5T. -/
theorem row2_m5_curve :
    ((5230162342299885741870882086387344043048282634471720194275 : ℚ) / (46342027807394779706754824216932672869339009439242435761 : ℚ)) ^ 2 =
      ((203327275043094961574407844319408428662 : ℚ) / (12901791593205736498578307160848081441 : ℚ)) ^ 3 + (-1 : ℚ) * ((203327275043094961574407844319408428662 : ℚ) / (12901791593205736498578307160848081441 : ℚ)) + (8839 : ℚ) := by
  norm_num

/-- Row 2, prime-local curve point 5T. -/
noncomputable def row2_m5_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (8839)) :=
  localCurvePoint 421 (-1) (8839)
    ((203327275043094961574407844319408428662 : ℚ) / (12901791593205736498578307160848081441 : ℚ)) ((5230162342299885741870882086387344043048282634471720194275 : ℚ) / (46342027807394779706754824216932672869339009439242435761 : ℚ))
    row2_m5_x row2_m5_y row2_m5_curve

#print axioms row2_m5_curve
#print axioms row2_m5_localPoint

/-- Row 3, rational curve equation for 1T. -/
theorem row3_m1_curve :
    ((55 : ℚ) / (1 : ℚ)) ^ 2 =
      ((-18 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((-18 : ℚ) / (1 : ℚ)) + (8839 : ℚ) := by
  norm_num

/-- Row 3, prime-local curve point 1T. -/
noncomputable def row3_m1_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (8839)) :=
  localCurvePoint 421 (-1) (8839)
    ((-18 : ℚ) / (1 : ℚ)) ((55 : ℚ) / (1 : ℚ))
    row3_m1_x row3_m1_y row3_m1_curve

#print axioms row3_m1_curve
#print axioms row3_m1_localPoint

/-- Row 3, rational curve equation for 2T. -/
theorem row3_m2_curve :
    ((-1623155011 : ℚ) / (1331000 : ℚ)) ^ 2 =
      ((1378441 : ℚ) / (12100 : ℚ)) ^ 3 + (-1 : ℚ) * ((1378441 : ℚ) / (12100 : ℚ)) + (8839 : ℚ) := by
  norm_num

/-- Row 3, prime-local curve point 2T. -/
noncomputable def row3_m2_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (8839)) :=
  localCurvePoint 421 (-1) (8839)
    ((1378441 : ℚ) / (12100 : ℚ)) ((-1623155011 : ℚ) / (1331000 : ℚ))
    row3_m2_x row3_m2_y row3_m2_curve

#print axioms row3_m2_curve
#print axioms row3_m2_localPoint

/-- Row 3, rational curve equation for 3T. -/
theorem row3_m3_curve :
    ((382064229689165922965 : ℚ) / (4067198651273825521 : ℚ)) ^ 2 =
      ((-6583384675258 : ℚ) / (2547985330081 : ℚ)) ^ 3 + (-1 : ℚ) * ((-6583384675258 : ℚ) / (2547985330081 : ℚ)) + (8839 : ℚ) := by
  norm_num

/-- Row 3, prime-local curve point 3T. -/
noncomputable def row3_m3_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (8839)) :=
  localCurvePoint 421 (-1) (8839)
    ((-6583384675258 : ℚ) / (2547985330081 : ℚ)) ((382064229689165922965 : ℚ) / (4067198651273825521 : ℚ))
    row3_m3_x row3_m3_y row3_m3_curve

#print axioms row3_m3_curve
#print axioms row3_m3_localPoint

/-- Row 3, rational curve equation for 4T. -/
theorem row3_m4_curve :
    ((-7675750746049392913879186847997204641 : ℚ) / (45535282262802338704778275892488000 : ℚ)) ^ 2 =
      ((3438256701666689140231361 : ℚ) / (127516197983145449856400 : ℚ)) ^ 3 + (-1 : ℚ) * ((3438256701666689140231361 : ℚ) / (127516197983145449856400 : ℚ)) + (8839 : ℚ) := by
  norm_num

/-- Row 3, prime-local curve point 4T. -/
noncomputable def row3_m4_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (8839)) :=
  localCurvePoint 421 (-1) (8839)
    ((3438256701666689140231361 : ℚ) / (127516197983145449856400 : ℚ)) ((-7675750746049392913879186847997204641 : ℚ) / (45535282262802338704778275892488000 : ℚ))
    row3_m4_x row3_m4_y row3_m4_curve

#print axioms row3_m4_curve
#print axioms row3_m4_localPoint

/-- Row 3, rational curve equation for 5T. -/
theorem row3_m5_curve :
    ((5230162342299885741870882086387344043048282634471720194275 : ℚ) / (46342027807394779706754824216932672869339009439242435761 : ℚ)) ^ 2 =
      ((203327275043094961574407844319408428662 : ℚ) / (12901791593205736498578307160848081441 : ℚ)) ^ 3 + (-1 : ℚ) * ((203327275043094961574407844319408428662 : ℚ) / (12901791593205736498578307160848081441 : ℚ)) + (8839 : ℚ) := by
  norm_num

/-- Row 3, prime-local curve point 5T. -/
noncomputable def row3_m5_localPoint :
    CurvePoint (localIntegers 421)
      ((algebraMap ℤ (localIntegers 421)) (-1))
      ((algebraMap ℤ (localIntegers 421)) (8839)) :=
  localCurvePoint 421 (-1) (8839)
    ((203327275043094961574407844319408428662 : ℚ) / (12901791593205736498578307160848081441 : ℚ)) ((5230162342299885741870882086387344043048282634471720194275 : ℚ) / (46342027807394779706754824216932672869339009439242435761 : ℚ))
    row3_m5_x row3_m5_y row3_m5_curve

#print axioms row3_m5_curve
#print axioms row3_m5_localPoint

/-- Row 4, rational curve equation for 1T. -/
theorem row4_m1_curve :
    ((55 : ℚ) / (1 : ℚ)) ^ 2 =
      ((74 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((74 : ℚ) / (1 : ℚ)) + (-402125 : ℚ) := by
  norm_num

/-- Row 4, prime-local curve point 1T. -/
noncomputable def row4_m1_localPoint :
    CurvePoint (localIntegers 431)
      ((algebraMap ℤ (localIntegers 431)) (-1))
      ((algebraMap ℤ (localIntegers 431)) (-402125)) :=
  localCurvePoint 431 (-1) (-402125)
    ((74 : ℚ) / (1 : ℚ)) ((55 : ℚ) / (1 : ℚ))
    row4_m1_x row4_m1_y row4_m1_curve

#print axioms row4_m1_curve
#print axioms row4_m1_localPoint

/-- Row 4, rational curve equation for 2T. -/
theorem row4_m2_curve :
    ((-4388712644083 : ℚ) / (1331000 : ℚ)) ^ 2 =
      ((268055529 : ℚ) / (12100 : ℚ)) ^ 3 + (-1 : ℚ) * ((268055529 : ℚ) / (12100 : ℚ)) + (-402125 : ℚ) := by
  norm_num

/-- Row 4, prime-local curve point 2T. -/
noncomputable def row4_m2_localPoint :
    CurvePoint (localIntegers 431)
      ((algebraMap ℤ (localIntegers 431)) (-1))
      ((algebraMap ℤ (localIntegers 431)) (-402125)) :=
  localCurvePoint 431 (-1) (-402125)
    ((268055529 : ℚ) / (12100 : ℚ)) ((-4388712644083 : ℚ) / (1331000 : ℚ))
    row4_m2_x row4_m2_y row4_m2_curve

#print axioms row4_m2_curve
#print axioms row4_m2_localPoint

/-- Row 4, rational curve equation for 3T. -/
theorem row4_m3_curve :
    ((3188682746729969714108227685 : ℚ) / (19068429851627524630826689 : ℚ)) ^ 2 =
      ((5387922401006760034 : ℚ) / (71374534527296641 : ℚ)) ^ 3 + (-1 : ℚ) * ((5387922401006760034 : ℚ) / (71374534527296641 : ℚ)) + (-402125 : ℚ) := by
  norm_num

/-- Row 4, prime-local curve point 3T. -/
noncomputable def row4_m3_localPoint :
    CurvePoint (localIntegers 431)
      ((algebraMap ℤ (localIntegers 431)) (-1))
      ((algebraMap ℤ (localIntegers 431)) (-402125)) :=
  localCurvePoint 431 (-1) (-402125)
    ((5387922401006760034 : ℚ) / (71374534527296641 : ℚ)) ((3188682746729969714108227685 : ℚ) / (19068429851627524630826689 : ℚ))
    row4_m3_x row4_m3_y row4_m3_curve

#print axioms row4_m3_curve
#print axioms row4_m3_localPoint

/-- Row 4, rational curve equation for 4T. -/
theorem row4_m4_curve :
    ((-370978116247191600373018823976168947479240947140321 : ℚ) / (900076618397221928979804718234299019491976000 : ℚ)) ^ 2 =
      ((5162965327273530105196293306185281 : ℚ) / (932222655740965456489687027600 : ℚ)) ^ 3 + (-1 : ℚ) * ((5162965327273530105196293306185281 : ℚ) / (932222655740965456489687027600 : ℚ)) + (-402125 : ℚ) := by
  norm_num

/-- Row 4, prime-local curve point 4T. -/
noncomputable def row4_m4_localPoint :
    CurvePoint (localIntegers 431)
      ((algebraMap ℤ (localIntegers 431)) (-1))
      ((algebraMap ℤ (localIntegers 431)) (-402125)) :=
  localCurvePoint 431 (-1) (-402125)
    ((5162965327273530105196293306185281 : ℚ) / (932222655740965456489687027600 : ℚ)) ((-370978116247191600373018823976168947479240947140321 : ℚ) / (900076618397221928979804718234299019491976000 : ℚ))
    row4_m4_x row4_m4_y row4_m4_curve

#print axioms row4_m4_curve
#print axioms row4_m4_localPoint

/-- Row 4, rational curve equation for 5T. -/
theorem row4_m5_curve :
    ((1984920116350474025621866961439010164745814223980413419723353646071078508831475 : ℚ) / (6931975045442833051440704986292403901193801048521101572522557172471985940769 : ℚ)) ^ 2 =
      ((28548170702994654678892103318010323052302636062331154 : ℚ) / (363556008871351419186551834580881163695550800022721 : ℚ)) ^ 3 + (-1 : ℚ) * ((28548170702994654678892103318010323052302636062331154 : ℚ) / (363556008871351419186551834580881163695550800022721 : ℚ)) + (-402125 : ℚ) := by
  norm_num

/-- Row 4, prime-local curve point 5T. -/
noncomputable def row4_m5_localPoint :
    CurvePoint (localIntegers 431)
      ((algebraMap ℤ (localIntegers 431)) (-1))
      ((algebraMap ℤ (localIntegers 431)) (-402125)) :=
  localCurvePoint 431 (-1) (-402125)
    ((28548170702994654678892103318010323052302636062331154 : ℚ) / (363556008871351419186551834580881163695550800022721 : ℚ)) ((1984920116350474025621866961439010164745814223980413419723353646071078508831475 : ℚ) / (6931975045442833051440704986292403901193801048521101572522557172471985940769 : ℚ))
    row4_m5_x row4_m5_y row4_m5_curve

#print axioms row4_m5_curve
#print axioms row4_m5_localPoint

/-- Row 4, rational curve equation for 6T. -/
theorem row4_m6_curve :
    ((-603991500435417954748293427508095676371361857303019778601377665358699396755408270413744910921565855730725504636403 : ℚ) / (4945826260696007571265068949381559223169043228020799575777038391481779422871131585487218130941566939224417000 : ℚ)) ^ 2 =
      ((7145365991815879796396298123030959614003082653777580397810681480917181275369 : ℚ) / (2902858750585395550743642419223349526588639025139844555396128246399852900 : ℚ)) ^ 3 + (-1 : ℚ) * ((7145365991815879796396298123030959614003082653777580397810681480917181275369 : ℚ) / (2902858750585395550743642419223349526588639025139844555396128246399852900 : ℚ)) + (-402125 : ℚ) := by
  norm_num

/-- Row 4, prime-local curve point 6T. -/
noncomputable def row4_m6_localPoint :
    CurvePoint (localIntegers 431)
      ((algebraMap ℤ (localIntegers 431)) (-1))
      ((algebraMap ℤ (localIntegers 431)) (-402125)) :=
  localCurvePoint 431 (-1) (-402125)
    ((7145365991815879796396298123030959614003082653777580397810681480917181275369 : ℚ) / (2902858750585395550743642419223349526588639025139844555396128246399852900 : ℚ)) ((-603991500435417954748293427508095676371361857303019778601377665358699396755408270413744910921565855730725504636403 : ℚ) / (4945826260696007571265068949381559223169043228020799575777038391481779422871131585487218130941566939224417000 : ℚ))
    row4_m6_x row4_m6_y row4_m6_curve

#print axioms row4_m6_curve
#print axioms row4_m6_localPoint

/-- Row 5, rational curve equation for 1T. -/
theorem row5_m1_curve :
    ((-99 : ℚ) / (1 : ℚ)) ^ 2 =
      ((-71 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((-71 : ℚ) / (1 : ℚ)) + (367641 : ℚ) := by
  norm_num

/-- Row 5, prime-local curve point 1T. -/
noncomputable def row5_m1_localPoint :
    CurvePoint (localIntegers 431)
      ((algebraMap ℤ (localIntegers 431)) (-1))
      ((algebraMap ℤ (localIntegers 431)) (367641)) :=
  localCurvePoint 431 (-1) (367641)
    ((-71 : ℚ) / (1 : ℚ)) ((-99 : ℚ) / (1 : ℚ))
    row5_m1_x row5_m1_y row5_m1_curve

#print axioms row5_m1_curve
#print axioms row5_m1_localPoint

/-- Row 5, rational curve equation for 2T. -/
theorem row5_m2_curve :
    ((448133200975 : ℚ) / (970299 : ℚ)) ^ 2 =
      ((58560463 : ℚ) / (9801 : ℚ)) ^ 3 + (-1 : ℚ) * ((58560463 : ℚ) / (9801 : ℚ)) + (367641 : ℚ) := by
  norm_num

/-- Row 5, prime-local curve point 2T. -/
noncomputable def row5_m2_localPoint :
    CurvePoint (localIntegers 431)
      ((algebraMap ℤ (localIntegers 431)) (-1))
      ((algebraMap ℤ (localIntegers 431)) (367641)) :=
  localCurvePoint 431 (-1) (367641)
    ((58560463 : ℚ) / (9801 : ℚ)) ((448133200975 : ℚ) / (970299 : ℚ))
    row5_m2_x row5_m2_y row5_m2_curve

#print axioms row5_m2_curve
#print axioms row5_m2_localPoint

/-- Row 5, rational curve equation for 3T. -/
theorem row5_m3_curve :
    ((-7368051614779236308136363 : ℚ) / (26008442870641274533463 : ℚ)) ^ 2 =
      ((-57933654361616144 : ℚ) / (877828279779889 : ℚ)) ^ 3 + (-1 : ℚ) * ((-57933654361616144 : ℚ) / (877828279779889 : ℚ)) + (367641 : ℚ) := by
  norm_num

/-- Row 5, prime-local curve point 3T. -/
noncomputable def row5_m3_localPoint :
    CurvePoint (localIntegers 431)
      ((algebraMap ℤ (localIntegers 431)) (-1))
      ((algebraMap ℤ (localIntegers 431)) (367641)) :=
  localCurvePoint 431 (-1) (367641)
    ((-57933654361616144 : ℚ) / (877828279779889 : ℚ)) ((-7368051614779236308136363 : ℚ) / (26008442870641274533463 : ℚ))
    row5_m3_x row5_m3_y row5_m3_curve

#print axioms row5_m3_curve
#print axioms row5_m3_localPoint

/-- Row 5, rational curve equation for 4T. -/
theorem row5_m4_curve :
    ((5041409006423232188577334905377997112196837723 : ℚ) / (87322657910838273907870234045885974703125 : ℚ)) ^ 2 =
      ((2940031961902148170312190574259 : ℚ) / (1968269808363593561057075625 : ℚ)) ^ 3 + (-1 : ℚ) * ((2940031961902148170312190574259 : ℚ) / (1968269808363593561057075625 : ℚ)) + (367641 : ℚ) := by
  norm_num

/-- Row 5, prime-local curve point 4T. -/
noncomputable def row5_m4_localPoint :
    CurvePoint (localIntegers 431)
      ((algebraMap ℤ (localIntegers 431)) (-1))
      ((algebraMap ℤ (localIntegers 431)) (367641)) :=
  localCurvePoint 431 (-1) (367641)
    ((2940031961902148170312190574259 : ℚ) / (1968269808363593561057075625 : ℚ)) ((5041409006423232188577334905377997112196837723 : ℚ) / (87322657910838273907870234045885974703125 : ℚ))
    row5_m4_x row5_m4_y row5_m4_curve

#print axioms row5_m4_curve
#print axioms row5_m4_localPoint

/-- Row 5, rational curve equation for 5T. -/
theorem row5_m5_curve :
    ((-60518923938482039050097222496079809290075928506073089384074508424564399 : ℚ) / (140395882596167911596787704235394708999059033326523220607510164350351 : ℚ)) ^ 2 =
      ((-153050858261739963318595662744447404008629354371 : ℚ) / (2701279861896846964723399309342058915835914401 : ℚ)) ^ 3 + (-1 : ℚ) * ((-153050858261739963318595662744447404008629354371 : ℚ) / (2701279861896846964723399309342058915835914401 : ℚ)) + (367641 : ℚ) := by
  norm_num

/-- Row 5, prime-local curve point 5T. -/
noncomputable def row5_m5_localPoint :
    CurvePoint (localIntegers 431)
      ((algebraMap ℤ (localIntegers 431)) (-1))
      ((algebraMap ℤ (localIntegers 431)) (367641)) :=
  localCurvePoint 431 (-1) (367641)
    ((-153050858261739963318595662744447404008629354371 : ℚ) / (2701279861896846964723399309342058915835914401 : ℚ)) ((-60518923938482039050097222496079809290075928506073089384074508424564399 : ℚ) / (140395882596167911596787704235394708999059033326523220607510164350351 : ℚ))
    row5_m5_x row5_m5_y row5_m5_curve

#print axioms row5_m5_curve
#print axioms row5_m5_localPoint

/-- Row 6, rational curve equation for 1T. -/
theorem row6_m1_curve :
    ((116 : ℚ) / (1 : ℚ)) ^ 2 =
      ((244 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((244 : ℚ) / (1 : ℚ)) + (-14513084 : ℚ) := by
  norm_num

/-- Row 6, prime-local curve point 1T. -/
noncomputable def row6_m1_localPoint :
    CurvePoint (localIntegers 593)
      ((algebraMap ℤ (localIntegers 593)) (-1))
      ((algebraMap ℤ (localIntegers 593)) (-14513084)) :=
  localCurvePoint 593 (-1) (-14513084)
    ((244 : ℚ) / (1 : ℚ)) ((116 : ℚ) / (1 : ℚ))
    row6_m1_x row6_m1_y row6_m1_curve

#print axioms row6_m1_curve
#print axioms row6_m1_localPoint

/-- Row 6, rational curve equation for 2T. -/
theorem row6_m2_curve :
    ((-5690610020727055 : ℚ) / (12487168 : ℚ)) ^ 2 =
      ((31874194337 : ℚ) / (53824 : ℚ)) ^ 3 + (-1 : ℚ) * ((31874194337 : ℚ) / (53824 : ℚ)) + (-14513084 : ℚ) := by
  norm_num

/-- Row 6, prime-local curve point 2T. -/
noncomputable def row6_m2_localPoint :
    CurvePoint (localIntegers 593)
      ((algebraMap ℤ (localIntegers 593)) (-1))
      ((algebraMap ℤ (localIntegers 593)) (-14513084)) :=
  localCurvePoint 593 (-1) (-14513084)
    ((31874194337 : ℚ) / (53824 : ℚ)) ((-5690610020727055 : ℚ) / (12487168 : ℚ))
    row6_m2_x row6_m2_y row6_m2_curve

#print axioms row6_m2_curve
#print axioms row6_m2_localPoint

/-- Row 6, rational curve equation for 3T. -/
theorem row6_m3_curve :
    ((11273943934553135634739758826800604 : ℚ) / (32343030754056651499867538051041 : ℚ)) ^ 2 =
      ((248303625919710742091124 : ℚ) / (1015127225951637360961 : ℚ)) ^ 3 + (-1 : ℚ) * ((248303625919710742091124 : ℚ) / (1015127225951637360961 : ℚ)) + (-14513084 : ℚ) := by
  norm_num

/-- Row 6, prime-local curve point 3T. -/
noncomputable def row6_m3_localPoint :
    CurvePoint (localIntegers 593)
      ((algebraMap ℤ (localIntegers 593)) (-1))
      ((algebraMap ℤ (localIntegers 593)) (-14513084)) :=
  localCurvePoint 593 (-1) (-14513084)
    ((248303625919710742091124 : ℚ) / (1015127225951637360961 : ℚ)) ((11273943934553135634739758826800604 : ℚ) / (32343030754056651499867538051041 : ℚ))
    row6_m3_x row6_m3_y row6_m3_curve

#print axioms row6_m3_curve
#print axioms row6_m3_localPoint

/-- Row 6, rational curve equation for 4T. -/
theorem row6_m4_curve :
    ((-1048661434270201964863215228516516831782289459107017768791798209 : ℚ) / (18409009190566559223151879267223519151232309083934208000 : ℚ)) ^ 2 =
      ((1032183387593894206310156518127567676728961 : ℚ) / (6971939498272590022700490328656390400 : ℚ)) ^ 3 + (-1 : ℚ) * ((1032183387593894206310156518127567676728961 : ℚ) / (6971939498272590022700490328656390400 : ℚ)) + (-14513084 : ℚ) := by
  norm_num

/-- Row 6, prime-local curve point 4T. -/
noncomputable def row6_m4_localPoint :
    CurvePoint (localIntegers 593)
      ((algebraMap ℤ (localIntegers 593)) (-1))
      ((algebraMap ℤ (localIntegers 593)) (-14513084)) :=
  localCurvePoint 593 (-1) (-14513084)
    ((1032183387593894206310156518127567676728961 : ℚ) / (6971939498272590022700490328656390400 : ℚ)) ((-1048661434270201964863215228516516831782289459107017768791798209 : ℚ) / (18409009190566559223151879267223519151232309083934208000 : ℚ))
    row6_m4_x row6_m4_y row6_m4_curve

#print axioms row6_m4_curve
#print axioms row6_m4_localPoint

/-- Row 7, rational curve equation for 1T. -/
theorem row7_m1_curve :
    ((45 : ℚ) / (1 : ℚ)) ^ 2 =
      ((-21 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((-21 : ℚ) / (1 : ℚ)) + (11265 : ℚ) := by
  norm_num

/-- Row 7, prime-local curve point 1T. -/
noncomputable def row7_m1_localPoint :
    CurvePoint (localIntegers 593)
      ((algebraMap ℤ (localIntegers 593)) (-1))
      ((algebraMap ℤ (localIntegers 593)) (11265)) :=
  localCurvePoint 593 (-1) (11265)
    ((-21 : ℚ) / (1 : ℚ)) ((45 : ℚ) / (1 : ℚ))
    row7_m1_x row7_m1_y row7_m1_curve

#print axioms row7_m1_curve
#print axioms row7_m1_localPoint

/-- Row 7, rational curve equation for 2T. -/
theorem row7_m2_curve :
    ((-377232481 : ℚ) / (91125 : ℚ)) ^ 2 =
      ((521971 : ℚ) / (2025 : ℚ)) ^ 3 + (-1 : ℚ) * ((521971 : ℚ) / (2025 : ℚ)) + (11265 : ℚ) := by
  norm_num

/-- Row 7, prime-local curve point 2T. -/
noncomputable def row7_m2_localPoint :
    CurvePoint (localIntegers 593)
      ((algebraMap ℤ (localIntegers 593)) (-1))
      ((algebraMap ℤ (localIntegers 593)) (11265)) :=
  localCurvePoint 593 (-1) (11265)
    ((521971 : ℚ) / (2025 : ℚ)) ((-377232481 : ℚ) / (91125 : ℚ))
    row7_m2_x row7_m2_y row7_m2_curve

#print axioms row7_m2_curve
#print axioms row7_m2_localPoint

/-- Row 7, rational curve equation for 3T. -/
theorem row7_m3_curve :
    ((2224828391772195045 : ℚ) / (22484985903636992 : ℚ)) ^ 2 =
      ((-909046829559 : ℚ) / (79663933504 : ℚ)) ^ 3 + (-1 : ℚ) * ((-909046829559 : ℚ) / (79663933504 : ℚ)) + (11265 : ℚ) := by
  norm_num

/-- Row 7, prime-local curve point 3T. -/
noncomputable def row7_m3_localPoint :
    CurvePoint (localIntegers 593)
      ((algebraMap ℤ (localIntegers 593)) (-1))
      ((algebraMap ℤ (localIntegers 593)) (11265)) :=
  localCurvePoint 593 (-1) (11265)
    ((-909046829559 : ℚ) / (79663933504 : ℚ)) ((2224828391772195045 : ℚ) / (22484985903636992 : ℚ))
    row7_m3_x row7_m3_y row7_m3_curve

#print axioms row7_m3_curve
#print axioms row7_m3_localPoint

/-- Row 7, rational curve equation for 4T. -/
theorem row7_m4_curve :
    ((-2561123432466711869149037309933087 : ℚ) / (4891755940113870458307890911125 : ℚ)) ^ 2 =
      ((18460664325611363435539 : ℚ) / (288166298060866106025 : ℚ)) ^ 3 + (-1 : ℚ) * ((18460664325611363435539 : ℚ) / (288166298060866106025 : ℚ)) + (11265 : ℚ) := by
  norm_num

/-- Row 7, prime-local curve point 4T. -/
noncomputable def row7_m4_localPoint :
    CurvePoint (localIntegers 593)
      ((algebraMap ℤ (localIntegers 593)) (-1))
      ((algebraMap ℤ (localIntegers 593)) (11265)) :=
  localCurvePoint 593 (-1) (11265)
    ((18460664325611363435539 : ℚ) / (288166298060866106025 : ℚ)) ((-2561123432466711869149037309933087 : ℚ) / (4891755940113870458307890911125 : ℚ))
    row7_m4_x row7_m4_y row7_m4_curve

#print axioms row7_m4_curve
#print axioms row7_m4_localPoint

/-- Row 7, rational curve equation for 5T. -/
theorem row7_m5_curve :
    ((8691153502809057703260710404033865416668267382386525 : ℚ) / (81877007268169902331613518854826448693441070607279 : ℚ)) ^ 2 =
      ((3042346341070290937182667730032299 : ℚ) / (1885564125489658322950803107942881 : ℚ)) ^ 3 + (-1 : ℚ) * ((3042346341070290937182667730032299 : ℚ) / (1885564125489658322950803107942881 : ℚ)) + (11265 : ℚ) := by
  norm_num

/-- Row 7, prime-local curve point 5T. -/
noncomputable def row7_m5_localPoint :
    CurvePoint (localIntegers 593)
      ((algebraMap ℤ (localIntegers 593)) (-1))
      ((algebraMap ℤ (localIntegers 593)) (11265)) :=
  localCurvePoint 593 (-1) (11265)
    ((3042346341070290937182667730032299 : ℚ) / (1885564125489658322950803107942881 : ℚ)) ((8691153502809057703260710404033865416668267382386525 : ℚ) / (81877007268169902331613518854826448693441070607279 : ℚ))
    row7_m5_x row7_m5_y row7_m5_curve

#print axioms row7_m5_curve
#print axioms row7_m5_localPoint

/-- Row 8, rational curve equation for 1T. -/
theorem row8_m1_curve :
    ((-105 : ℚ) / (1 : ℚ)) ^ 2 =
      ((38 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((38 : ℚ) / (1 : ℚ)) + (-43809 : ℚ) := by
  norm_num

/-- Row 8, prime-local curve point 1T. -/
noncomputable def row8_m1_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-43809)) :=
  localCurvePoint 617 (-1) (-43809)
    ((38 : ℚ) / (1 : ℚ)) ((-105 : ℚ) / (1 : ℚ))
    row8_m1_x row8_m1_y row8_m1_curve

#print axioms row8_m1_curve
#print axioms row8_m1_localPoint

/-- Row 8, rational curve equation for 2T. -/
theorem row8_m2_curve :
    ((60437732291 : ℚ) / (9261000 : ℚ)) ^ 2 =
      ((15405961 : ℚ) / (44100 : ℚ)) ^ 3 + (-1 : ℚ) * ((15405961 : ℚ) / (44100 : ℚ)) + (-43809 : ℚ) := by
  norm_num

/-- Row 8, prime-local curve point 2T. -/
noncomputable def row8_m2_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-43809)) :=
  localCurvePoint 617 (-1) (-43809)
    ((15405961 : ℚ) / (44100 : ℚ)) ((60437732291 : ℚ) / (9261000 : ℚ))
    row8_m2_x row8_m2_y row8_m2_curve

#print axioms row8_m2_curve
#print axioms row8_m2_localPoint

/-- Row 8, rational curve equation for 3T. -/
theorem row8_m3_curve :
    ((-1287046380940914897601515 : ℚ) / (2588373169798390163281 : ℚ)) ^ 2 =
      ((12494266189331198 : ℚ) / (188517321085921 : ℚ)) ^ 3 + (-1 : ℚ) * ((12494266189331198 : ℚ) / (188517321085921 : ℚ)) + (-43809 : ℚ) := by
  norm_num

/-- Row 8, prime-local curve point 3T. -/
noncomputable def row8_m3_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-43809)) :=
  localCurvePoint 617 (-1) (-43809)
    ((12494266189331198 : ℚ) / (188517321085921 : ℚ)) ((-1287046380940914897601515 : ℚ) / (2588373169798390163281 : ℚ))
    row8_m3_x row8_m3_y row8_m3_curve

#print axioms row8_m3_curve
#print axioms row8_m3_localPoint

/-- Row 8, rational curve equation for 4T. -/
theorem row8_m4_curve :
    ((13094606713922665698176364198687071763929761 : ℚ) / (16355821156186337695411316049931053048000 : ℚ)) ^ 2 =
      ((56796005927401135774548277441 : ℚ) / (644339717062022236771328400 : ℚ)) ^ 3 + (-1 : ℚ) * ((56796005927401135774548277441 : ℚ) / (644339717062022236771328400 : ℚ)) + (-43809 : ℚ) := by
  norm_num

/-- Row 8, prime-local curve point 4T. -/
noncomputable def row8_m4_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-43809)) :=
  localCurvePoint 617 (-1) (-43809)
    ((56796005927401135774548277441 : ℚ) / (644339717062022236771328400 : ℚ)) ((13094606713922665698176364198687071763929761 : ℚ) / (16355821156186337695411316049931053048000 : ℚ))
    row8_m4_x row8_m4_y row8_m4_curve

#print axioms row8_m4_curve
#print axioms row8_m4_localPoint

/-- Row 8, rational curve equation for 5T. -/
theorem row8_m5_curve :
    ((-36758965460302761014237370305635891378074066019775833315080833586525 : ℚ) / (13032514202247095792864166693250575859247766430309404023943257041 : ℚ)) ^ 2 =
      ((1107577519376036142457855960034396635132291118 : ℚ) / (5537989626569737798826138757489037006644961 : ℚ)) ^ 3 + (-1 : ℚ) * ((1107577519376036142457855960034396635132291118 : ℚ) / (5537989626569737798826138757489037006644961 : ℚ)) + (-43809 : ℚ) := by
  norm_num

/-- Row 8, prime-local curve point 5T. -/
noncomputable def row8_m5_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-43809)) :=
  localCurvePoint 617 (-1) (-43809)
    ((1107577519376036142457855960034396635132291118 : ℚ) / (5537989626569737798826138757489037006644961 : ℚ)) ((-36758965460302761014237370305635891378074066019775833315080833586525 : ℚ) / (13032514202247095792864166693250575859247766430309404023943257041 : ℚ))
    row8_m5_x row8_m5_y row8_m5_curve

#print axioms row8_m5_curve
#print axioms row8_m5_localPoint

/-- Row 8, rational curve equation for 6T. -/
theorem row8_m6_curve :
    ((8339120452210102621802497949262846290478751317197691652946208549375563611850317586338651822534211 : ℚ) / (44146824457589803172988106013529634153340012598614218265888243454265315157577055142487834687000 : ℚ)) ^ 2 =
      ((53717540720992004281528751926262834581439494429504659250979535241 : ℚ) / (1249107012277294596331201021060053544353657942282235275684108900 : ℚ)) ^ 3 + (-1 : ℚ) * ((53717540720992004281528751926262834581439494429504659250979535241 : ℚ) / (1249107012277294596331201021060053544353657942282235275684108900 : ℚ)) + (-43809 : ℚ) := by
  norm_num

/-- Row 8, prime-local curve point 6T. -/
noncomputable def row8_m6_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-43809)) :=
  localCurvePoint 617 (-1) (-43809)
    ((53717540720992004281528751926262834581439494429504659250979535241 : ℚ) / (1249107012277294596331201021060053544353657942282235275684108900 : ℚ)) ((8339120452210102621802497949262846290478751317197691652946208549375563611850317586338651822534211 : ℚ) / (44146824457589803172988106013529634153340012598614218265888243454265315157577055142487834687000 : ℚ))
    row8_m6_x row8_m6_y row8_m6_curve

#print axioms row8_m6_curve
#print axioms row8_m6_localPoint

/-- Row 9, rational curve equation for 1T. -/
theorem row9_m1_curve :
    ((308 : ℚ) / (1 : ℚ)) ^ 2 =
      ((261 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((261 : ℚ) / (1 : ℚ)) + (-17684456 : ℚ) := by
  norm_num

/-- Row 9, prime-local curve point 1T. -/
noncomputable def row9_m1_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-17684456)) :=
  localCurvePoint 617 (-1) (-17684456)
    ((261 : ℚ) / (1 : ℚ)) ((308 : ℚ) / (1 : ℚ))
    row9_m1_x row9_m1_y row9_m1_curve

#print axioms row9_m1_curve
#print axioms row9_m1_localPoint

/-- Row 9, rational curve equation for 2T. -/
theorem row9_m2_curve :
    ((-1059286549339565 : ℚ) / (29218112 : ℚ)) ^ 2 =
      ((10391437753 : ℚ) / (94864 : ℚ)) ^ 3 + (-1 : ℚ) * ((10391437753 : ℚ) / (94864 : ℚ)) + (-17684456 : ℚ) := by
  norm_num

/-- Row 9, prime-local curve point 2T. -/
noncomputable def row9_m2_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-17684456)) :=
  localCurvePoint 617 (-1) (-17684456)
    ((10391437753 : ℚ) / (94864 : ℚ)) ((-1059286549339565 : ℚ) / (29218112 : ℚ))
    row9_m2_x row9_m2_y row9_m2_curve

#print axioms row9_m2_curve
#print axioms row9_m2_localPoint

/-- Row 9, rational curve equation for 3T. -/
theorem row9_m3_curve :
    ((1039285552371268731974037226976188 : ℚ) / (1114086363816676154481171472249 : ℚ)) ^ 2 =
      ((28451105313539807242901 : ℚ) / (107468017918289706001 : ℚ)) ^ 3 + (-1 : ℚ) * ((28451105313539807242901 : ℚ) / (107468017918289706001 : ℚ)) + (-17684456 : ℚ) := by
  norm_num

/-- Row 9, prime-local curve point 3T. -/
noncomputable def row9_m3_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-17684456)) :=
  localCurvePoint 617 (-1) (-17684456)
    ((28451105313539807242901 : ℚ) / (107468017918289706001 : ℚ)) ((1039285552371268731974037226976188 : ℚ) / (1114086363816676154481171472249 : ℚ))
    row9_m3_x row9_m3_y row9_m3_curve

#print axioms row9_m3_curve
#print axioms row9_m3_localPoint

/-- Row 9, rational curve equation for 4T. -/
theorem row9_m4_curve :
    ((-1259081160166101662510180793829825620304891461016196600769809 : ℚ) / (277832156342127433877043668074336508043120125305664000 : ℚ)) ^ 2 =
      ((11660108953853336201345504815689538046561 : ℚ) / (425783021703929839417041373037761600 : ℚ)) ^ 3 + (-1 : ℚ) * ((11660108953853336201345504815689538046561 : ℚ) / (425783021703929839417041373037761600 : ℚ)) + (-17684456 : ℚ) := by
  norm_num

/-- Row 9, prime-local curve point 4T. -/
noncomputable def row9_m4_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-17684456)) :=
  localCurvePoint 617 (-1) (-17684456)
    ((11660108953853336201345504815689538046561 : ℚ) / (425783021703929839417041373037761600 : ℚ)) ((-1259081160166101662510180793829825620304891461016196600769809 : ℚ) / (277832156342127433877043668074336508043120125305664000 : ℚ))
    row9_m4_x row9_m4_y row9_m4_curve

#print axioms row9_m4_curve
#print axioms row9_m4_localPoint

/-- Row 9, rational curve equation for 5T. -/
theorem row9_m5_curve :
    ((2191411656408890346645206825641093211391913080022522659846541836163760827977120407595331776932 : ℚ) / (1382649122587203852496818432788056627709073607948576506639388520492128914678695914800822569 : ℚ)) ^ 2 =
      ((337988436817574174917161768163438789580368321226426754389621941 : ℚ) / (1241103465409720491924394360649176342883558435011170949193521 : ℚ)) ^ 3 + (-1 : ℚ) * ((337988436817574174917161768163438789580368321226426754389621941 : ℚ) / (1241103465409720491924394360649176342883558435011170949193521 : ℚ)) + (-17684456 : ℚ) := by
  norm_num

/-- Row 9, prime-local curve point 5T. -/
noncomputable def row9_m5_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-17684456)) :=
  localCurvePoint 617 (-1) (-17684456)
    ((337988436817574174917161768163438789580368321226426754389621941 : ℚ) / (1241103465409720491924394360649176342883558435011170949193521 : ℚ)) ((2191411656408890346645206825641093211391913080022522659846541836163760827977120407595331776932 : ℚ) / (1382649122587203852496818432788056627709073607948576506639388520492128914678695914800822569 : ℚ))
    row9_m5_x row9_m5_y row9_m5_curve

#print axioms row9_m5_curve
#print axioms row9_m5_localPoint

/-- Row 10, rational curve equation for 1T. -/
theorem row10_m1_curve :
    ((65 : ℚ) / (1 : ℚ)) ^ 2 =
      ((66 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((66 : ℚ) / (1 : ℚ)) + (-283205 : ℚ) := by
  norm_num

/-- Row 10, prime-local curve point 1T. -/
noncomputable def row10_m1_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-283205)) :=
  localCurvePoint 617 (-1) (-283205)
    ((66 : ℚ) / (1 : ℚ)) ((65 : ℚ) / (1 : ℚ))
    row10_m1_x row10_m1_y row10_m1_curve

#print axioms row10_m1_curve
#print axioms row10_m1_localPoint

/-- Row 10, rational curve equation for 2T. -/
theorem row10_m2_curve :
    ((-2187562381363 : ℚ) / (2197000 : ℚ)) ^ 2 =
      ((168515689 : ℚ) / (16900 : ℚ)) ^ 3 + (-1 : ℚ) * ((168515689 : ℚ) / (16900 : ℚ)) + (-283205 : ℚ) := by
  norm_num

/-- Row 10, prime-local curve point 2T. -/
noncomputable def row10_m2_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-283205)) :=
  localCurvePoint 617 (-1) (-283205)
    ((168515689 : ℚ) / (16900 : ℚ)) ((-2187562381363 : ℚ) / (2197000 : ℚ))
    row10_m2_x row10_m2_y row10_m2_curve

#print axioms row10_m2_curve
#print axioms row10_m2_localPoint

/-- Row 10, rational curve equation for 3T. -/
theorem row10_m3_curve :
    ((939375576686745620595777955 : ℚ) / (4691034319774864270337569 : ℚ)) ^ 2 =
      ((1923448154470781786 : ℚ) / (28022856757283521 : ℚ)) ^ 3 + (-1 : ℚ) * ((1923448154470781786 : ℚ) / (28022856757283521 : ℚ)) + (-283205 : ℚ) := by
  norm_num

/-- Row 10, prime-local curve point 3T. -/
noncomputable def row10_m3_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-283205)) :=
  localCurvePoint 617 (-1) (-283205)
    ((1923448154470781786 : ℚ) / (28022856757283521 : ℚ)) ((939375576686745620595777955 : ℚ) / (4691034319774864270337569 : ℚ))
    row10_m3_x row10_m3_y row10_m3_curve

#print axioms row10_m3_curve
#print axioms row10_m3_localPoint

/-- Row 10, rational curve equation for 4T. -/
theorem row10_m4_curve :
    ((-22900213924363980638125882526342662627796571067361 : ℚ) / (183993034919643542301592977314972717807672000 : ℚ)) ^ 2 =
      ((806421991684684438668121251787841 : ℚ) / (323495012051168218802273184400 : ℚ)) ^ 3 + (-1 : ℚ) * ((806421991684684438668121251787841 : ℚ) / (323495012051168218802273184400 : ℚ)) + (-283205 : ℚ) := by
  norm_num

/-- Row 10, prime-local curve point 4T. -/
noncomputable def row10_m4_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-283205)) :=
  localCurvePoint 617 (-1) (-283205)
    ((806421991684684438668121251787841 : ℚ) / (323495012051168218802273184400 : ℚ)) ((-22900213924363980638125882526342662627796571067361 : ℚ) / (183993034919643542301592977314972717807672000 : ℚ))
    row10_m4_x row10_m4_y row10_m4_curve

#print axioms row10_m4_curve
#print axioms row10_m4_localPoint

/-- Row 10, rational curve equation for 5T. -/
theorem row10_m5_curve :
    ((36341684508764889366899015208153066079251181429836758250382414986789092737925 : ℚ) / (103147505036316021213084967636005767077727192553887683659947357874940211009 : ℚ)) ^ 2 =
      ((1630488298802039025398697815937546477113568968380426 : ℚ) / (21994080911207863176672171123220061322592458149761 : ℚ)) ^ 3 + (-1 : ℚ) * ((1630488298802039025398697815937546477113568968380426 : ℚ) / (21994080911207863176672171123220061322592458149761 : ℚ)) + (-283205 : ℚ) := by
  norm_num

/-- Row 10, prime-local curve point 5T. -/
noncomputable def row10_m5_localPoint :
    CurvePoint (localIntegers 617)
      ((algebraMap ℤ (localIntegers 617)) (-1))
      ((algebraMap ℤ (localIntegers 617)) (-283205)) :=
  localCurvePoint 617 (-1) (-283205)
    ((1630488298802039025398697815937546477113568968380426 : ℚ) / (21994080911207863176672171123220061322592458149761 : ℚ)) ((36341684508764889366899015208153066079251181429836758250382414986789092737925 : ℚ) / (103147505036316021213084967636005767077727192553887683659947357874940211009 : ℚ))
    row10_m5_x row10_m5_y row10_m5_curve

#print axioms row10_m5_curve
#print axioms row10_m5_localPoint

/-- Row 11, rational curve equation for 1T. -/
theorem row11_m1_curve :
    ((163 : ℚ) / (1 : ℚ)) ^ 2 =
      ((148 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((148 : ℚ) / (1 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 11, prime-local curve point 1T. -/
noncomputable def row11_m1_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((148 : ℚ) / (1 : ℚ)) ((163 : ℚ) / (1 : ℚ))
    row11_m1_x row11_m1_y row11_m1_curve

#print axioms row11_m1_curve
#print axioms row11_m1_localPoint

/-- Row 11, rational curve equation for 2T. -/
theorem row11_m2_curve :
    ((-280640833321735 : ℚ) / (34645976 : ℚ)) ^ 2 =
      ((4286477825 : ℚ) / (106276 : ℚ)) ^ 3 + (-1 : ℚ) * ((4286477825 : ℚ) / (106276 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 11, prime-local curve point 2T. -/
noncomputable def row11_m2_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((4286477825 : ℚ) / (106276 : ℚ)) ((-280640833321735 : ℚ) / (34645976 : ℚ))
    row11_m2_x row11_m2_y row11_m2_curve

#print axioms row11_m2_curve
#print axioms row11_m2_localPoint

/-- Row 11, rational curve equation for 3T. -/
theorem row11_m3_curve :
    ((38655122451616601803601636928281 : ℚ) / (77895458254631512077609650833 : ℚ)) ^ 2 =
      ((2759066700437090304012 : ℚ) / (18239296824546546529 : ℚ)) ^ 3 + (-1 : ℚ) * ((2759066700437090304012 : ℚ) / (18239296824546546529 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 11, prime-local curve point 3T. -/
noncomputable def row11_m3_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((2759066700437090304012 : ℚ) / (18239296824546546529 : ℚ)) ((38655122451616601803601636928281 : ℚ) / (77895458254631512077609650833 : ℚ))
    row11_m3_x row11_m3_y row11_m3_curve

#print axioms row11_m3_curve
#print axioms row11_m3_localPoint

/-- Row 11, rational curve equation for 4T. -/
theorem row11_m4_curve :
    ((-6203018282660121348025985593570301494304626150503247476401 : ℚ) / (6126259246060229600475274061714646939447244019848000 : ℚ)) ^ 2 =
      ((337600045281186242884078180866016397601 : ℚ) / (33480883829037146369435007780288400 : ℚ)) ^ 3 + (-1 : ℚ) * ((337600045281186242884078180866016397601 : ℚ) / (33480883829037146369435007780288400 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 11, prime-local curve point 4T. -/
noncomputable def row11_m4_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((337600045281186242884078180866016397601 : ℚ) / (33480883829037146369435007780288400 : ℚ)) ((-6203018282660121348025985593570301494304626150503247476401 : ℚ) / (6126259246060229600475274061714646939447244019848000 : ℚ))
    row11_m4_x row11_m4_y row11_m4_curve

#print axioms row11_m4_curve
#print axioms row11_m4_localPoint

/-- Row 11, rational curve equation for 5T. -/
theorem row11_m5_curve :
    ((402611498305165319482828521345367522951686687598289261969381135554623423426299812757049151 : ℚ) / (472531072090516843116161014137090729433434705868052742195624631491936416743960113722897 : ℚ)) ^ 2 =
      ((958288067373392353238562897984543674316568343919026866020092 : ℚ) / (6066714828897980109441699217816433249333984967110849052769 : ℚ)) ^ 3 + (-1 : ℚ) * ((958288067373392353238562897984543674316568343919026866020092 : ℚ) / (6066714828897980109441699217816433249333984967110849052769 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 11, prime-local curve point 5T. -/
noncomputable def row11_m5_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((958288067373392353238562897984543674316568343919026866020092 : ℚ) / (6066714828897980109441699217816433249333984967110849052769 : ℚ)) ((402611498305165319482828521345367522951686687598289261969381135554623423426299812757049151 : ℚ) / (472531072090516843116161014137090729433434705868052742195624631491936416743960113722897 : ℚ))
    row11_m5_x row11_m5_y row11_m5_curve

#print axioms row11_m5_curve
#print axioms row11_m5_localPoint

/-- Row 11, rational curve equation for 6T. -/
theorem row11_m6_curve :
    ((-10798244330200809659961292562200131109105647229452351623305664663177270305484019276304530783662386763479138820031579859597198248295 : ℚ) / (35993434051658193834158238451393269410839796796740193603822842319162264889277787406968875575749022651637534211858156979841224 : ℚ)) ^ 2 =
      ((488548043422916456163125373970459094842081641073285201735759450775655922516943429241025 : ℚ) / (109013978366979636574061529706853911973445864890024159687797541282099287425092081476 : ℚ)) ^ 3 + (-1 : ℚ) * ((488548043422916456163125373970459094842081641073285201735759450775655922516943429241025 : ℚ) / (109013978366979636574061529706853911973445864890024159687797541282099287425092081476 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 11, prime-local curve point 6T. -/
noncomputable def row11_m6_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((488548043422916456163125373970459094842081641073285201735759450775655922516943429241025 : ℚ) / (109013978366979636574061529706853911973445864890024159687797541282099287425092081476 : ℚ)) ((-10798244330200809659961292562200131109105647229452351623305664663177270305484019276304530783662386763479138820031579859597198248295 : ℚ) / (35993434051658193834158238451393269410839796796740193603822842319162264889277787406968875575749022651637534211858156979841224 : ℚ))
    row11_m6_x row11_m6_y row11_m6_curve

#print axioms row11_m6_curve
#print axioms row11_m6_localPoint

/-- Row 12, rational curve equation for 1T. -/
theorem row12_m1_curve :
    ((163 : ℚ) / (1 : ℚ)) ^ 2 =
      ((148 : ℚ) / (1 : ℚ)) ^ 3 + (-1 : ℚ) * ((148 : ℚ) / (1 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 12, prime-local curve point 1T. -/
noncomputable def row12_m1_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((148 : ℚ) / (1 : ℚ)) ((163 : ℚ) / (1 : ℚ))
    row12_m1_x row12_m1_y row12_m1_curve

#print axioms row12_m1_curve
#print axioms row12_m1_localPoint

/-- Row 12, rational curve equation for 2T. -/
theorem row12_m2_curve :
    ((-280640833321735 : ℚ) / (34645976 : ℚ)) ^ 2 =
      ((4286477825 : ℚ) / (106276 : ℚ)) ^ 3 + (-1 : ℚ) * ((4286477825 : ℚ) / (106276 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 12, prime-local curve point 2T. -/
noncomputable def row12_m2_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((4286477825 : ℚ) / (106276 : ℚ)) ((-280640833321735 : ℚ) / (34645976 : ℚ))
    row12_m2_x row12_m2_y row12_m2_curve

#print axioms row12_m2_curve
#print axioms row12_m2_localPoint

/-- Row 12, rational curve equation for 3T. -/
theorem row12_m3_curve :
    ((38655122451616601803601636928281 : ℚ) / (77895458254631512077609650833 : ℚ)) ^ 2 =
      ((2759066700437090304012 : ℚ) / (18239296824546546529 : ℚ)) ^ 3 + (-1 : ℚ) * ((2759066700437090304012 : ℚ) / (18239296824546546529 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 12, prime-local curve point 3T. -/
noncomputable def row12_m3_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((2759066700437090304012 : ℚ) / (18239296824546546529 : ℚ)) ((38655122451616601803601636928281 : ℚ) / (77895458254631512077609650833 : ℚ))
    row12_m3_x row12_m3_y row12_m3_curve

#print axioms row12_m3_curve
#print axioms row12_m3_localPoint

/-- Row 12, rational curve equation for 4T. -/
theorem row12_m4_curve :
    ((-6203018282660121348025985593570301494304626150503247476401 : ℚ) / (6126259246060229600475274061714646939447244019848000 : ℚ)) ^ 2 =
      ((337600045281186242884078180866016397601 : ℚ) / (33480883829037146369435007780288400 : ℚ)) ^ 3 + (-1 : ℚ) * ((337600045281186242884078180866016397601 : ℚ) / (33480883829037146369435007780288400 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 12, prime-local curve point 4T. -/
noncomputable def row12_m4_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((337600045281186242884078180866016397601 : ℚ) / (33480883829037146369435007780288400 : ℚ)) ((-6203018282660121348025985593570301494304626150503247476401 : ℚ) / (6126259246060229600475274061714646939447244019848000 : ℚ))
    row12_m4_x row12_m4_y row12_m4_curve

#print axioms row12_m4_curve
#print axioms row12_m4_localPoint

/-- Row 12, rational curve equation for 5T. -/
theorem row12_m5_curve :
    ((402611498305165319482828521345367522951686687598289261969381135554623423426299812757049151 : ℚ) / (472531072090516843116161014137090729433434705868052742195624631491936416743960113722897 : ℚ)) ^ 2 =
      ((958288067373392353238562897984543674316568343919026866020092 : ℚ) / (6066714828897980109441699217816433249333984967110849052769 : ℚ)) ^ 3 + (-1 : ℚ) * ((958288067373392353238562897984543674316568343919026866020092 : ℚ) / (6066714828897980109441699217816433249333984967110849052769 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 12, prime-local curve point 5T. -/
noncomputable def row12_m5_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((958288067373392353238562897984543674316568343919026866020092 : ℚ) / (6066714828897980109441699217816433249333984967110849052769 : ℚ)) ((402611498305165319482828521345367522951686687598289261969381135554623423426299812757049151 : ℚ) / (472531072090516843116161014137090729433434705868052742195624631491936416743960113722897 : ℚ))
    row12_m5_x row12_m5_y row12_m5_curve

#print axioms row12_m5_curve
#print axioms row12_m5_localPoint

/-- Row 12, rational curve equation for 6T. -/
theorem row12_m6_curve :
    ((-10798244330200809659961292562200131109105647229452351623305664663177270305484019276304530783662386763479138820031579859597198248295 : ℚ) / (35993434051658193834158238451393269410839796796740193603822842319162264889277787406968875575749022651637534211858156979841224 : ℚ)) ^ 2 =
      ((488548043422916456163125373970459094842081641073285201735759450775655922516943429241025 : ℚ) / (109013978366979636574061529706853911973445864890024159687797541282099287425092081476 : ℚ)) ^ 3 + (-1 : ℚ) * ((488548043422916456163125373970459094842081641073285201735759450775655922516943429241025 : ℚ) / (109013978366979636574061529706853911973445864890024159687797541282099287425092081476 : ℚ)) + (-3215075 : ℚ) := by
  norm_num

/-- Row 12, prime-local curve point 6T. -/
noncomputable def row12_m6_localPoint :
    CurvePoint (localIntegers 677)
      ((algebraMap ℤ (localIntegers 677)) (-1))
      ((algebraMap ℤ (localIntegers 677)) (-3215075)) :=
  localCurvePoint 677 (-1) (-3215075)
    ((488548043422916456163125373970459094842081641073285201735759450775655922516943429241025 : ℚ) / (109013978366979636574061529706853911973445864890024159687797541282099287425092081476 : ℚ)) ((-10798244330200809659961292562200131109105647229452351623305664663177270305484019276304530783662386763479138820031579859597198248295 : ℚ) / (35993434051658193834158238451393269410839796796740193603822842319162264889277787406968875575749022651637534211858156979841224 : ℚ))
    row12_m6_x row12_m6_y row12_m6_curve

#print axioms row12_m6_curve
#print axioms row12_m6_localPoint

end XedniCurveEquationCertificates
