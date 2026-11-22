import ExactChainMultipliers

namespace XedniPublicPointReduction

open XedniLocalZModReduction XedniRationalLocalWitness
open XedniRegularChainReduction XedniCurveEquationCertificates
open XedniCoordinateCertificates

local instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩

-- BEGIN GENERATED ROWS
-- Frozen source SHA-256: a34dd1b580483815d7f4dc61877eae9935b16873b8f9bc908b24c2e51a25154e

local instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 421) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 431) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 593) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 617) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 677) := ⟨by norm_num⟩

/-- Row 0, 1T: reduced x coordinate. -/
theorem row0_m1_x_public :
    (mapPoint (reduceZMod 313) row0_m1_localPoint).x = (306 : ZMod 313) := by
  change reduceZMod 313 (toLocal 313 ((-7 : ℚ) / (1 : ℚ)) row0_m1_x) = 306
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row0_m1_x_public

/-- Row 0, 1T: reduced y coordinate. -/
theorem row0_m1_y_public :
    (mapPoint (reduceZMod 313) row0_m1_localPoint).y = (125 : ZMod 313) := by
  change reduceZMod 313 (toLocal 313 ((125 : ℚ) / (1 : ℚ)) row0_m1_y) = 125
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row0_m1_y_public

/-- Row 0, 4T: reduced x coordinate. -/
theorem row0_m4_x_public :
    (mapPoint (reduceZMod 313) row0_m4_localPoint).x = (1 : ZMod 313) := by
  change reduceZMod 313 (toLocal 313 ((-26650279307333340077261 : ℚ) / (1126296815249629515625 : ℚ)) row0_m4_x) = 1
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row0_m4_x_public

/-- Row 0, 4T: reduced y coordinate. -/
theorem row0_m4_y_public :
    (mapPoint (reduceZMod 313) row0_m4_localPoint).y = (183 : ZMod 313) := by
  change reduceZMod 313 (toLocal 313 ((1977418304204033859577942351663013 : ℚ) / (37798910677688541009983716796875 : ℚ)) row0_m4_y) = 183
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row0_m4_y_public

/-- Row 1, 1T: reduced x coordinate. -/
theorem row1_m1_x_public :
    (mapPoint (reduceZMod 421) row1_m1_localPoint).x = (211 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((-210 : ℚ) / (1 : ℚ)) row1_m1_x) = 211
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row1_m1_x_public

/-- Row 1, 1T: reduced y coordinate. -/
theorem row1_m1_y_public :
    (mapPoint (reduceZMod 421) row1_m1_localPoint).y = (114 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((114 : ℚ) / (1 : ℚ)) row1_m1_y) = 114
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row1_m1_y_public

/-- Row 1, 4T: reduced x coordinate. -/
theorem row1_m4_x_public :
    (mapPoint (reduceZMod 421) row1_m4_localPoint).x = (49 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((94323106859153273434564086544158054420577 : ℚ) / (1119162781685499416647242528284403264 : ℚ)) row1_m4_x) = 49
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row1_m4_x_public

/-- Row 1, 4T: reduced y coordinate. -/
theorem row1_m4_y_public :
    (mapPoint (reduceZMod 421) row1_m4_localPoint).y = (308 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((-28968576138357017202042244440043053790221957208391810185307665 : ℚ) / (1183967792886266316779962539649724586898400986070681088 : ℚ)) row1_m4_y) = 308
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row1_m4_y_public

/-- Row 1, 5T: reduced x coordinate. -/
theorem row1_m5_x_public :
    (mapPoint (reduceZMod 421) row1_m5_localPoint).x = (177 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((-6037892091791484835810617682772208834049779090336529551651651666 : ℚ) / (29076880704459317355937847032965558435335406229818019164082129 : ℚ)) row1_m5_x) = 177
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row1_m5_x_public

/-- Row 1, 5T: reduced y coordinate. -/
theorem row1_m5_y_public :
    (mapPoint (reduceZMod 421) row1_m5_localPoint).y = (22 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((88706460511322288237480609867404970395792531213416032466242832798579163925728238955386128233642 : ℚ) / (156791213713274487384947970675768732930766209404878727572455822047852757664006201919811652633 : ℚ)) row1_m5_y) = 22
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row1_m5_y_public

/-- Row 2, 1T: reduced x coordinate. -/
theorem row2_m1_x_public :
    (mapPoint (reduceZMod 421) row2_m1_localPoint).x = (403 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((-18 : ℚ) / (1 : ℚ)) row2_m1_x) = 403
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row2_m1_x_public

/-- Row 2, 1T: reduced y coordinate. -/
theorem row2_m1_y_public :
    (mapPoint (reduceZMod 421) row2_m1_localPoint).y = (55 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((55 : ℚ) / (1 : ℚ)) row2_m1_y) = 55
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row2_m1_y_public

/-- Row 2, 5T: reduced x coordinate. -/
theorem row2_m5_x_public :
    (mapPoint (reduceZMod 421) row2_m5_localPoint).x = (162 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((203327275043094961574407844319408428662 : ℚ) / (12901791593205736498578307160848081441 : ℚ)) row2_m5_x) = 162
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row2_m5_x_public

/-- Row 2, 5T: reduced y coordinate. -/
theorem row2_m5_y_public :
    (mapPoint (reduceZMod 421) row2_m5_localPoint).y = (37 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((5230162342299885741870882086387344043048282634471720194275 : ℚ) / (46342027807394779706754824216932672869339009439242435761 : ℚ)) row2_m5_y) = 37
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row2_m5_y_public

/-- Row 3, 1T: reduced x coordinate. -/
theorem row3_m1_x_public :
    (mapPoint (reduceZMod 421) row3_m1_localPoint).x = (403 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((-18 : ℚ) / (1 : ℚ)) row3_m1_x) = 403
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row3_m1_x_public

/-- Row 3, 1T: reduced y coordinate. -/
theorem row3_m1_y_public :
    (mapPoint (reduceZMod 421) row3_m1_localPoint).y = (55 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((55 : ℚ) / (1 : ℚ)) row3_m1_y) = 55
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row3_m1_y_public

/-- Row 3, 3T: reduced x coordinate. -/
theorem row3_m3_x_public :
    (mapPoint (reduceZMod 421) row3_m3_localPoint).x = (203 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((-6583384675258 : ℚ) / (2547985330081 : ℚ)) row3_m3_x) = 203
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row3_m3_x_public

/-- Row 3, 3T: reduced y coordinate. -/
theorem row3_m3_y_public :
    (mapPoint (reduceZMod 421) row3_m3_localPoint).y = (164 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((382064229689165922965 : ℚ) / (4067198651273825521 : ℚ)) row3_m3_y) = 164
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row3_m3_y_public

/-- Row 3, 5T: reduced x coordinate. -/
theorem row3_m5_x_public :
    (mapPoint (reduceZMod 421) row3_m5_localPoint).x = (162 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((203327275043094961574407844319408428662 : ℚ) / (12901791593205736498578307160848081441 : ℚ)) row3_m5_x) = 162
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row3_m5_x_public

/-- Row 3, 5T: reduced y coordinate. -/
theorem row3_m5_y_public :
    (mapPoint (reduceZMod 421) row3_m5_localPoint).y = (37 : ZMod 421) := by
  change reduceZMod 421 (toLocal 421 ((5230162342299885741870882086387344043048282634471720194275 : ℚ) / (46342027807394779706754824216932672869339009439242435761 : ℚ)) row3_m5_y) = 37
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row3_m5_y_public

/-- Row 4, 1T: reduced x coordinate. -/
theorem row4_m1_x_public :
    (mapPoint (reduceZMod 431) row4_m1_localPoint).x = (74 : ZMod 431) := by
  change reduceZMod 431 (toLocal 431 ((74 : ℚ) / (1 : ℚ)) row4_m1_x) = 74
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row4_m1_x_public

/-- Row 4, 1T: reduced y coordinate. -/
theorem row4_m1_y_public :
    (mapPoint (reduceZMod 431) row4_m1_localPoint).y = (55 : ZMod 431) := by
  change reduceZMod 431 (toLocal 431 ((55 : ℚ) / (1 : ℚ)) row4_m1_y) = 55
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row4_m1_y_public

/-- Row 4, 5T: reduced x coordinate. -/
theorem row4_m5_x_public :
    (mapPoint (reduceZMod 431) row4_m5_localPoint).x = (303 : ZMod 431) := by
  change reduceZMod 431 (toLocal 431 ((28548170702994654678892103318010323052302636062331154 : ℚ) / (363556008871351419186551834580881163695550800022721 : ℚ)) row4_m5_x) = 303
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row4_m5_x_public

/-- Row 4, 5T: reduced y coordinate. -/
theorem row4_m5_y_public :
    (mapPoint (reduceZMod 431) row4_m5_localPoint).y = (282 : ZMod 431) := by
  change reduceZMod 431 (toLocal 431 ((1984920116350474025621866961439010164745814223980413419723353646071078508831475 : ℚ) / (6931975045442833051440704986292403901193801048521101572522557172471985940769 : ℚ)) row4_m5_y) = 282
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row4_m5_y_public

/-- Row 4, 6T: reduced x coordinate. -/
theorem row4_m6_x_public :
    (mapPoint (reduceZMod 431) row4_m6_localPoint).x = (144 : ZMod 431) := by
  change reduceZMod 431 (toLocal 431 ((7145365991815879796396298123030959614003082653777580397810681480917181275369 : ℚ) / (2902858750585395550743642419223349526588639025139844555396128246399852900 : ℚ)) row4_m6_x) = 144
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row4_m6_x_public

/-- Row 4, 6T: reduced y coordinate. -/
theorem row4_m6_y_public :
    (mapPoint (reduceZMod 431) row4_m6_localPoint).y = (45 : ZMod 431) := by
  change reduceZMod 431 (toLocal 431 ((-603991500435417954748293427508095676371361857303019778601377665358699396755408270413744910921565855730725504636403 : ℚ) / (4945826260696007571265068949381559223169043228020799575777038391481779422871131585487218130941566939224417000 : ℚ)) row4_m6_y) = 45
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row4_m6_y_public

/-- Row 5, 1T: reduced x coordinate. -/
theorem row5_m1_x_public :
    (mapPoint (reduceZMod 431) row5_m1_localPoint).x = (360 : ZMod 431) := by
  change reduceZMod 431 (toLocal 431 ((-71 : ℚ) / (1 : ℚ)) row5_m1_x) = 360
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row5_m1_x_public

/-- Row 5, 1T: reduced y coordinate. -/
theorem row5_m1_y_public :
    (mapPoint (reduceZMod 431) row5_m1_localPoint).y = (332 : ZMod 431) := by
  change reduceZMod 431 (toLocal 431 ((-99 : ℚ) / (1 : ℚ)) row5_m1_y) = 332
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row5_m1_y_public

/-- Row 5, 5T: reduced x coordinate. -/
theorem row5_m5_x_public :
    (mapPoint (reduceZMod 431) row5_m5_localPoint).x = (376 : ZMod 431) := by
  change reduceZMod 431 (toLocal 431 ((-153050858261739963318595662744447404008629354371 : ℚ) / (2701279861896846964723399309342058915835914401 : ℚ)) row5_m5_x) = 376
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row5_m5_x_public

/-- Row 5, 5T: reduced y coordinate. -/
theorem row5_m5_y_public :
    (mapPoint (reduceZMod 431) row5_m5_localPoint).y = (123 : ZMod 431) := by
  change reduceZMod 431 (toLocal 431 ((-60518923938482039050097222496079809290075928506073089384074508424564399 : ℚ) / (140395882596167911596787704235394708999059033326523220607510164350351 : ℚ)) row5_m5_y) = 123
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row5_m5_y_public

/-- Row 6, 1T: reduced x coordinate. -/
theorem row6_m1_x_public :
    (mapPoint (reduceZMod 593) row6_m1_localPoint).x = (244 : ZMod 593) := by
  change reduceZMod 593 (toLocal 593 ((244 : ℚ) / (1 : ℚ)) row6_m1_x) = 244
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row6_m1_x_public

/-- Row 6, 1T: reduced y coordinate. -/
theorem row6_m1_y_public :
    (mapPoint (reduceZMod 593) row6_m1_localPoint).y = (116 : ZMod 593) := by
  change reduceZMod 593 (toLocal 593 ((116 : ℚ) / (1 : ℚ)) row6_m1_y) = 116
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row6_m1_y_public

/-- Row 6, 4T: reduced x coordinate. -/
theorem row6_m4_x_public :
    (mapPoint (reduceZMod 593) row6_m4_localPoint).x = (435 : ZMod 593) := by
  change reduceZMod 593 (toLocal 593 ((1032183387593894206310156518127567676728961 : ℚ) / (6971939498272590022700490328656390400 : ℚ)) row6_m4_x) = 435
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row6_m4_x_public

/-- Row 6, 4T: reduced y coordinate. -/
theorem row6_m4_y_public :
    (mapPoint (reduceZMod 593) row6_m4_localPoint).y = (391 : ZMod 593) := by
  change reduceZMod 593 (toLocal 593 ((-1048661434270201964863215228516516831782289459107017768791798209 : ℚ) / (18409009190566559223151879267223519151232309083934208000 : ℚ)) row6_m4_y) = 391
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row6_m4_y_public

/-- Row 7, 1T: reduced x coordinate. -/
theorem row7_m1_x_public :
    (mapPoint (reduceZMod 593) row7_m1_localPoint).x = (572 : ZMod 593) := by
  change reduceZMod 593 (toLocal 593 ((-21 : ℚ) / (1 : ℚ)) row7_m1_x) = 572
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row7_m1_x_public

/-- Row 7, 1T: reduced y coordinate. -/
theorem row7_m1_y_public :
    (mapPoint (reduceZMod 593) row7_m1_localPoint).y = (45 : ZMod 593) := by
  change reduceZMod 593 (toLocal 593 ((45 : ℚ) / (1 : ℚ)) row7_m1_y) = 45
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row7_m1_y_public

/-- Row 7, 5T: reduced x coordinate. -/
theorem row7_m5_x_public :
    (mapPoint (reduceZMod 593) row7_m5_localPoint).x = (92 : ZMod 593) := by
  change reduceZMod 593 (toLocal 593 ((3042346341070290937182667730032299 : ℚ) / (1885564125489658322950803107942881 : ℚ)) row7_m5_x) = 92
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row7_m5_x_public

/-- Row 7, 5T: reduced y coordinate. -/
theorem row7_m5_y_public :
    (mapPoint (reduceZMod 593) row7_m5_localPoint).y = (551 : ZMod 593) := by
  change reduceZMod 593 (toLocal 593 ((8691153502809057703260710404033865416668267382386525 : ℚ) / (81877007268169902331613518854826448693441070607279 : ℚ)) row7_m5_y) = 551
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row7_m5_y_public

/-- Row 8, 1T: reduced x coordinate. -/
theorem row8_m1_x_public :
    (mapPoint (reduceZMod 617) row8_m1_localPoint).x = (38 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((38 : ℚ) / (1 : ℚ)) row8_m1_x) = 38
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row8_m1_x_public

/-- Row 8, 1T: reduced y coordinate. -/
theorem row8_m1_y_public :
    (mapPoint (reduceZMod 617) row8_m1_localPoint).y = (512 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((-105 : ℚ) / (1 : ℚ)) row8_m1_y) = 512
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row8_m1_y_public

/-- Row 8, 6T: reduced x coordinate. -/
theorem row8_m6_x_public :
    (mapPoint (reduceZMod 617) row8_m6_localPoint).x = (378 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((53717540720992004281528751926262834581439494429504659250979535241 : ℚ) / (1249107012277294596331201021060053544353657942282235275684108900 : ℚ)) row8_m6_x) = 378
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row8_m6_x_public

/-- Row 8, 6T: reduced y coordinate. -/
theorem row8_m6_y_public :
    (mapPoint (reduceZMod 617) row8_m6_localPoint).y = (181 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((8339120452210102621802497949262846290478751317197691652946208549375563611850317586338651822534211 : ℚ) / (44146824457589803172988106013529634153340012598614218265888243454265315157577055142487834687000 : ℚ)) row8_m6_y) = 181
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row8_m6_y_public

/-- Row 9, 1T: reduced x coordinate. -/
theorem row9_m1_x_public :
    (mapPoint (reduceZMod 617) row9_m1_localPoint).x = (261 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((261 : ℚ) / (1 : ℚ)) row9_m1_x) = 261
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row9_m1_x_public

/-- Row 9, 1T: reduced y coordinate. -/
theorem row9_m1_y_public :
    (mapPoint (reduceZMod 617) row9_m1_localPoint).y = (308 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((308 : ℚ) / (1 : ℚ)) row9_m1_y) = 308
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row9_m1_y_public

/-- Row 9, 3T: reduced x coordinate. -/
theorem row9_m3_x_public :
    (mapPoint (reduceZMod 617) row9_m3_localPoint).x = (327 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((28451105313539807242901 : ℚ) / (107468017918289706001 : ℚ)) row9_m3_x) = 327
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row9_m3_x_public

/-- Row 9, 3T: reduced y coordinate. -/
theorem row9_m3_y_public :
    (mapPoint (reduceZMod 617) row9_m3_localPoint).y = (609 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((1039285552371268731974037226976188 : ℚ) / (1114086363816676154481171472249 : ℚ)) row9_m3_y) = 609
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row9_m3_y_public

/-- Row 9, 5T: reduced x coordinate. -/
theorem row9_m5_x_public :
    (mapPoint (reduceZMod 617) row9_m5_localPoint).x = (542 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((337988436817574174917161768163438789580368321226426754389621941 : ℚ) / (1241103465409720491924394360649176342883558435011170949193521 : ℚ)) row9_m5_x) = 542
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row9_m5_x_public

/-- Row 9, 5T: reduced y coordinate. -/
theorem row9_m5_y_public :
    (mapPoint (reduceZMod 617) row9_m5_localPoint).y = (289 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((2191411656408890346645206825641093211391913080022522659846541836163760827977120407595331776932 : ℚ) / (1382649122587203852496818432788056627709073607948576506639388520492128914678695914800822569 : ℚ)) row9_m5_y) = 289
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row9_m5_y_public

/-- Row 10, 1T: reduced x coordinate. -/
theorem row10_m1_x_public :
    (mapPoint (reduceZMod 617) row10_m1_localPoint).x = (66 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((66 : ℚ) / (1 : ℚ)) row10_m1_x) = 66
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row10_m1_x_public

/-- Row 10, 1T: reduced y coordinate. -/
theorem row10_m1_y_public :
    (mapPoint (reduceZMod 617) row10_m1_localPoint).y = (65 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((65 : ℚ) / (1 : ℚ)) row10_m1_y) = 65
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row10_m1_y_public

/-- Row 10, 4T: reduced x coordinate. -/
theorem row10_m4_x_public :
    (mapPoint (reduceZMod 617) row10_m4_localPoint).x = (590 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((806421991684684438668121251787841 : ℚ) / (323495012051168218802273184400 : ℚ)) row10_m4_x) = 590
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row10_m4_x_public

/-- Row 10, 4T: reduced y coordinate. -/
theorem row10_m4_y_public :
    (mapPoint (reduceZMod 617) row10_m4_localPoint).y = (324 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((-22900213924363980638125882526342662627796571067361 : ℚ) / (183993034919643542301592977314972717807672000 : ℚ)) row10_m4_y) = 324
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row10_m4_y_public

/-- Row 10, 5T: reduced x coordinate. -/
theorem row10_m5_x_public :
    (mapPoint (reduceZMod 617) row10_m5_localPoint).x = (338 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((1630488298802039025398697815937546477113568968380426 : ℚ) / (21994080911207863176672171123220061322592458149761 : ℚ)) row10_m5_x) = 338
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row10_m5_x_public

/-- Row 10, 5T: reduced y coordinate. -/
theorem row10_m5_y_public :
    (mapPoint (reduceZMod 617) row10_m5_localPoint).y = (248 : ZMod 617) := by
  change reduceZMod 617 (toLocal 617 ((36341684508764889366899015208153066079251181429836758250382414986789092737925 : ℚ) / (103147505036316021213084967636005767077727192553887683659947357874940211009 : ℚ)) row10_m5_y) = 248
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row10_m5_y_public

/-- Row 11, 1T: reduced x coordinate. -/
theorem row11_m1_x_public :
    (mapPoint (reduceZMod 677) row11_m1_localPoint).x = (148 : ZMod 677) := by
  change reduceZMod 677 (toLocal 677 ((148 : ℚ) / (1 : ℚ)) row11_m1_x) = 148
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row11_m1_x_public

/-- Row 11, 1T: reduced y coordinate. -/
theorem row11_m1_y_public :
    (mapPoint (reduceZMod 677) row11_m1_localPoint).y = (163 : ZMod 677) := by
  change reduceZMod 677 (toLocal 677 ((163 : ℚ) / (1 : ℚ)) row11_m1_y) = 163
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row11_m1_y_public

/-- Row 11, 6T: reduced x coordinate. -/
theorem row11_m6_x_public :
    (mapPoint (reduceZMod 677) row11_m6_localPoint).x = (541 : ZMod 677) := by
  change reduceZMod 677 (toLocal 677 ((488548043422916456163125373970459094842081641073285201735759450775655922516943429241025 : ℚ) / (109013978366979636574061529706853911973445864890024159687797541282099287425092081476 : ℚ)) row11_m6_x) = 541
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row11_m6_x_public

/-- Row 11, 6T: reduced y coordinate. -/
theorem row11_m6_y_public :
    (mapPoint (reduceZMod 677) row11_m6_localPoint).y = (42 : ZMod 677) := by
  change reduceZMod 677 (toLocal 677 ((-10798244330200809659961292562200131109105647229452351623305664663177270305484019276304530783662386763479138820031579859597198248295 : ℚ) / (35993434051658193834158238451393269410839796796740193603822842319162264889277787406968875575749022651637534211858156979841224 : ℚ)) row11_m6_y) = 42
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row11_m6_y_public

/-- Row 12, 1T: reduced x coordinate. -/
theorem row12_m1_x_public :
    (mapPoint (reduceZMod 677) row12_m1_localPoint).x = (148 : ZMod 677) := by
  change reduceZMod 677 (toLocal 677 ((148 : ℚ) / (1 : ℚ)) row12_m1_x) = 148
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row12_m1_x_public

/-- Row 12, 1T: reduced y coordinate. -/
theorem row12_m1_y_public :
    (mapPoint (reduceZMod 677) row12_m1_localPoint).y = (163 : ZMod 677) := by
  change reduceZMod 677 (toLocal 677 ((163 : ℚ) / (1 : ℚ)) row12_m1_y) = 163
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row12_m1_y_public

/-- Row 12, 6T: reduced x coordinate. -/
theorem row12_m6_x_public :
    (mapPoint (reduceZMod 677) row12_m6_localPoint).x = (541 : ZMod 677) := by
  change reduceZMod 677 (toLocal 677 ((488548043422916456163125373970459094842081641073285201735759450775655922516943429241025 : ℚ) / (109013978366979636574061529706853911973445864890024159687797541282099287425092081476 : ℚ)) row12_m6_x) = 541
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row12_m6_x_public

/-- Row 12, 6T: reduced y coordinate. -/
theorem row12_m6_y_public :
    (mapPoint (reduceZMod 677) row12_m6_localPoint).y = (42 : ZMod 677) := by
  change reduceZMod 677 (toLocal 677 ((-10798244330200809659961292562200131109105647229452351623305664663177270305484019276304530783662386763479138820031579859597198248295 : ℚ) / (35993434051658193834158238451393269410839796796740193603822842319162264889277787406968875575749022651637534211858156979841224 : ℚ)) row12_m6_y) = 42
  rw [reduce_rational]
  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))

#print axioms row12_m6_y_public
-- END GENERATED ROWS

end XedniPublicPointReduction
