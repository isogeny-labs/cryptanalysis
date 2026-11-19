import RecordedCertifiedRelation
import PublicPointReduction
import Mathlib.Tactic

/-! Initial formalization of the row-zero public base. The order computation
is retained as an exact replay in check_row0_point_order.py while the Lean
group-operation certificate remains open. -/

namespace XedniRecordedPointOrder

open XedniRegularChainReduction XedniRegularGroupLaw
open XedniAffineReductionBridge
open XedniCertifiedRelationExtraction XedniRecordedCertifiedRelation
open XedniLocalZModReduction XedniCurveEquationCertificates
open XedniPublicPointReduction XedniFiniteGroupChains

local instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩
local instance : Fact (Nat.Prime 331) := ⟨by norm_num⟩
local instance : (shortCurve (-1 : ZMod 313) 15961).IsElliptic :=
  row0_elliptic
local instance :
    (shortCurve
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) (-1)))
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) (15961)))).IsElliptic := by
  simpa [reduce_integer, map_ofNat] using row0_elliptic

def finiteBase : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨306, 125, by decide⟩

def basePoint : (shortCurve (-1 : ZMod 313) 15961).toAffine.Point :=
  toGroupPoint finiteBase

private theorem curvePoint_ext {P Q : CurvePoint (ZMod 313) (-1) 15961}
    (hx : P.x = Q.x) (hy : P.y = Q.y) : P = Q := by
  cases P with
  | mk x y h =>
      cases Q with
      | mk x' y' h' =>
          simpa only [CurvePoint.mk.injEq] using And.intro hx hy

theorem basePoint_ne_zero : basePoint ≠ 0 := by
  simp [basePoint, toGroupPoint, WeierstrassCurve.Affine.Point.mk]

def finiteDouble : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨214, 99, by decide⟩

theorem finite_double_step : FieldStep finiteBase finiteBase finiteDouble := by
  have hslope : (280907 : ZMod 313) / 250 = 261 := by
    apply (div_eq_iff (by decide : (250 : ZMod 313) ≠ 0)).2
    norm_num; decide
  right
  refine ⟨rfl, by decide, ?_, ?_⟩
  · norm_num [finiteBase, finiteDouble, addX, hslope]; decide
  · norm_num [finiteBase, finiteDouble, addY, addX, hslope]; decide

theorem basePoint_double :
    toGroupPoint finiteDouble = basePoint + basePoint := by
  exact fieldStep_group_add finite_double_step


def point4 : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨1, 183, by decide⟩

theorem double_2_4 : FieldStep finiteDouble finiteDouble point4 := by
  have hslope : (137387 : ZMod 313) / 198 = 41 := by
    apply (div_eq_iff (by decide : (198 : ZMod 313) ≠ 0)).2
    norm_num; decide
  right
  refine ⟨rfl, by decide, ?_, ?_⟩
  · norm_num [finiteDouble, point4, addX, hslope]; decide
  · norm_num [finiteDouble, point4, addY, addX, hslope]; decide

theorem point4_eq_double :
    toGroupPoint point4 = toGroupPoint finiteDouble + toGroupPoint finiteDouble :=
  fieldStep_group_add double_2_4

def point8 : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨154, 201, by decide⟩

theorem step_4_4_8 : FieldStep point4 point4 point8 := by
  have hslope : (2 : ZMod 313) / (366 : ZMod 313) = 65 := by
    apply (div_eq_iff (by decide : (366 : ZMod 313) ≠ 0)).2
    norm_num; decide
  right
  refine ⟨rfl, by decide, ?_, ?_⟩
  · norm_num [point4, point4, point8, addX, hslope]; decide
  · norm_num [point4, point4, point8, addY, addX, hslope]; decide

theorem add_4_4_8 :
    toGroupPoint point8 = toGroupPoint point4 + toGroupPoint point4 :=
  fieldStep_group_add step_4_4_8

def point16 : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨101, 134, by decide⟩

theorem step_8_8_16 : FieldStep point8 point8 point16 := by
  have hslope : (71147 : ZMod 313) / (402 : ZMod 313) = 89 := by
    apply (div_eq_iff (by decide : (402 : ZMod 313) ≠ 0)).2
    norm_num; decide
  right
  refine ⟨rfl, by decide, ?_, ?_⟩
  · norm_num [point8, point8, point16, addX, hslope]; decide
  · norm_num [point8, point8, point16, addY, addX, hslope]; decide

theorem add_8_8_16 :
    toGroupPoint point16 = toGroupPoint point8 + toGroupPoint point8 :=
  fieldStep_group_add step_8_8_16

def point32 : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨76, 219, by decide⟩

theorem step_16_16_32 : FieldStep point16 point16 point32 := by
  have hslope : (30602 : ZMod 313) / (268 : ZMod 313) = 252 := by
    apply (div_eq_iff (by decide : (268 : ZMod 313) ≠ 0)).2
    norm_num; decide
  right
  refine ⟨rfl, by decide, ?_, ?_⟩
  · norm_num [point16, point16, point32, addX, hslope]; decide
  · norm_num [point16, point16, point32, addY, addX, hslope]; decide

theorem add_16_16_32 :
    toGroupPoint point32 = toGroupPoint point16 + toGroupPoint point16 :=
  fieldStep_group_add step_16_16_32

def point64 : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨135, 269, by decide⟩

theorem step_32_32_64 : FieldStep point32 point32 point64 := by
  have hslope : (17327 : ZMod 313) / (438 : ZMod 313) = 66 := by
    apply (div_eq_iff (by decide : (438 : ZMod 313) ≠ 0)).2
    norm_num; decide
  right
  refine ⟨rfl, by decide, ?_, ?_⟩
  · norm_num [point32, point32, point64, addX, hslope]; decide
  · norm_num [point32, point32, point64, addY, addX, hslope]; decide

theorem add_32_32_64 :
    toGroupPoint point64 = toGroupPoint point32 + toGroupPoint point32 :=
  fieldStep_group_add step_32_32_64

def point128 : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨118, 188, by decide⟩

theorem step_64_64_128 : FieldStep point64 point64 point128 := by
  have hslope : (54674 : ZMod 313) / (538 : ZMod 313) = 211 := by
    apply (div_eq_iff (by decide : (538 : ZMod 313) ≠ 0)).2
    norm_num; decide
  right
  refine ⟨rfl, by decide, ?_, ?_⟩
  · norm_num [point64, point64, point128, addX, hslope]; decide
  · norm_num [point64, point64, point128, addY, addX, hslope]; decide

theorem add_64_64_128 :
    toGroupPoint point128 = toGroupPoint point64 + toGroupPoint point64 :=
  fieldStep_group_add step_64_64_128

def point256 : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨276, 62, by decide⟩

theorem step_128_128_256 : FieldStep point128 point128 point256 := by
  have hslope : (41771 : ZMod 313) / (376 : ZMod 313) = 42 := by
    apply (div_eq_iff (by decide : (376 : ZMod 313) ≠ 0)).2
    norm_num; decide
  right
  refine ⟨rfl, by decide, ?_, ?_⟩
  · norm_num [point128, point128, point256, addX, hslope]; decide
  · norm_num [point128, point128, point256, addY, addX, hslope]; decide

theorem add_128_128_256 :
    toGroupPoint point256 = toGroupPoint point128 + toGroupPoint point128 :=
  fieldStep_group_add step_128_128_256

def point320 : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨10, 7, by decide⟩

theorem step_256_64_320 : FieldStep point256 point64 point320 := by
  have hslope : (207 : ZMod 313) / (-141 : ZMod 313) = 185 := by
    apply (div_eq_iff (by decide : (-141 : ZMod 313) ≠ 0)).2
    norm_num; decide
  left
  refine ⟨by decide, ?_, ?_⟩
  · norm_num [point256, point64, point320, addX, hslope]; decide
  · norm_num [point256, point64, point320, addY, addX, hslope]; decide

theorem add_256_64_320 :
    toGroupPoint point320 = toGroupPoint point256 + toGroupPoint point64 :=
  fieldStep_group_add step_256_64_320

def point328 : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨158, 124, by decide⟩

theorem step_320_8_328 : FieldStep point320 point8 point328 := by
  have hslope : (194 : ZMod 313) / (144 : ZMod 313) = 310 := by
    apply (div_eq_iff (by decide : (144 : ZMod 313) ≠ 0)).2
    norm_num; decide
  left
  refine ⟨by decide, ?_, ?_⟩
  · norm_num [point320, point8, point328, addX, hslope]; decide
  · norm_num [point320, point8, point328, addY, addX, hslope]; decide

theorem add_320_8_328 :
    toGroupPoint point328 = toGroupPoint point320 + toGroupPoint point8 :=
  fieldStep_group_add step_320_8_328

def point330 : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨306, 188, by decide⟩

theorem step_328_2_330 : FieldStep point328 finiteDouble point330 := by
  have hslope : (-25 : ZMod 313) / (56 : ZMod 313) = 184 := by
    apply (div_eq_iff (by decide : (56 : ZMod 313) ≠ 0)).2
    norm_num; decide
  left
  refine ⟨by decide, ?_, ?_⟩
  · norm_num [point328, finiteDouble, point330, addX, hslope]; decide
  · norm_num [point328, finiteDouble, point330, addY, addX, hslope]; decide

theorem add_328_2_330 :
    toGroupPoint point330 = toGroupPoint point328 + toGroupPoint finiteDouble :=
  fieldStep_group_add step_328_2_330

theorem point2_scalar : toGroupPoint finiteDouble = 2 • basePoint := by
  rw [basePoint_double]
  abel

theorem point4_scalar : toGroupPoint point4 = 4 • basePoint := by
  rw [point4_eq_double, point2_scalar]
  abel

theorem point8_scalar : toGroupPoint point8 = 8 • basePoint := by
  rw [add_4_4_8, point4_scalar]
  abel

theorem point16_scalar : toGroupPoint point16 = 16 • basePoint := by
  rw [add_8_8_16, point8_scalar]
  abel

theorem point32_scalar : toGroupPoint point32 = 32 • basePoint := by
  rw [add_16_16_32, point16_scalar]
  abel

theorem point64_scalar : toGroupPoint point64 = 64 • basePoint := by
  rw [add_32_32_64, point32_scalar]
  abel

theorem point128_scalar : toGroupPoint point128 = 128 • basePoint := by
  rw [add_64_64_128, point64_scalar]
  abel

theorem point256_scalar : toGroupPoint point256 = 256 • basePoint := by
  rw [add_128_128_256, point128_scalar]
  abel

theorem point320_scalar : toGroupPoint point320 = 320 • basePoint := by
  rw [add_256_64_320, point256_scalar, point64_scalar]
  abel

theorem point328_scalar : toGroupPoint point328 = 328 • basePoint := by
  rw [add_320_8_328, point320_scalar, point8_scalar]
  abel

theorem point330_scalar : toGroupPoint point330 = 330 • basePoint := by
  rw [add_328_2_330, point328_scalar, point2_scalar]
  abel

theorem point330_eq_neg : toGroupPoint point330 = -basePoint := by
  unfold basePoint toGroupPoint
  simp only [WeierstrassCurve.Affine.Point.mk,
    WeierstrassCurve.Affine.Point.neg_some,
    WeierstrassCurve.Affine.Point.some.injEq]
  constructor
  · rfl
  · norm_num [point330, finiteBase, shortCurve, WeierstrassCurve.Affine.negY]
    decide

theorem basePoint_mul331 : (331 : ℕ) • basePoint = 0 := by
  calc
    (331 : ℕ) • basePoint = 330 • basePoint + basePoint := by abel
    _ = toGroupPoint point330 + basePoint := by rw [point330_scalar]
    _ = -basePoint + basePoint := by rw [point330_eq_neg]
    _ = 0 := neg_add_cancel _

theorem basePoint_order : addOrderOf basePoint = 331 :=
  addOrderOf_eq_prime basePoint_mul331 basePoint_ne_zero

noncomputable def recordedFiniteBase : CurvePoint (ZMod 313) (-1) 15961 :=
  ⟨(mapPoint (reduceZMod 313) row0_m1_localPoint).x,
   (mapPoint (reduceZMod 313) row0_m1_localPoint).y,
   by simpa [reduce_integer, map_ofNat] using
     (mapPoint (reduceZMod 313) row0_m1_localPoint).onCurve⟩

theorem recordedFiniteBase_x : recordedFiniteBase.x = 306 := by
  exact row0_m1_x_public

theorem recordedFiniteBase_y : recordedFiniteBase.y = 125 := by
  exact row0_m1_y_public

theorem recordedFiniteBase_eq : recordedFiniteBase = finiteBase := by
  have hx : recordedFiniteBase.x = finiteBase.x := by
    simpa [finiteBase] using recordedFiniteBase_x
  have hy : recordedFiniteBase.y = finiteBase.y := by
    simpa [finiteBase] using recordedFiniteBase_y
  exact curvePoint_ext hx hy

theorem recordedFiniteBase_order :
    addOrderOf (toGroupPoint recordedFiniteBase) = 331 := by
  rw [recordedFiniteBase_eq]
  exact basePoint_order

#print axioms basePoint_ne_zero
#print axioms finite_double_step
#print axioms basePoint_double
#print axioms double_2_4
#print axioms point4_eq_double
#print axioms step_4_4_8
#print axioms add_4_4_8
#print axioms step_8_8_16
#print axioms add_8_8_16
#print axioms step_16_16_32
#print axioms add_16_16_32
#print axioms step_32_32_64
#print axioms add_32_32_64
#print axioms step_64_64_128
#print axioms add_64_64_128
#print axioms step_128_128_256
#print axioms add_128_128_256
#print axioms step_256_64_320
#print axioms add_256_64_320
#print axioms step_320_8_328
#print axioms add_320_8_328
#print axioms step_328_2_330
#print axioms add_328_2_330
#print axioms point2_scalar
#print axioms point4_scalar
#print axioms point8_scalar
#print axioms point16_scalar
#print axioms point32_scalar
#print axioms point64_scalar
#print axioms point128_scalar
#print axioms point256_scalar
#print axioms point320_scalar
#print axioms point328_scalar
#print axioms point330_scalar
#print axioms point330_eq_neg
#print axioms basePoint_mul331
#print axioms basePoint_order
#print axioms recordedFiniteBase_x
#print axioms recordedFiniteBase_y
#print axioms recordedFiniteBase_eq
#print axioms recordedFiniteBase_order

end XedniRecordedPointOrder
