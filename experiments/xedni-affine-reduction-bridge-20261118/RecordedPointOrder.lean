import RecordedCertifiedRelation
import PublicPointReduction
import Mathlib.Tactic

/-! Initial formalization of the row-zero public base. The order computation
is retained as an exact replay in check_row0_point_order.py while the Lean
group-operation certificate remains open. -/

namespace XedniRecordedPointOrder

open XedniRegularChainReduction XedniRegularGroupLaw
open XedniCertifiedRelationExtraction XedniRecordedCertifiedRelation
open XedniLocalZModReduction XedniCurveEquationCertificates
open XedniPublicPointReduction XedniFiniteGroupChains

local instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩
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

theorem basePoint_ne_zero : basePoint ≠ 0 := by
  simp [basePoint, toGroupPoint, WeierstrassCurve.Affine.Point.mk]

#print axioms basePoint_ne_zero

end XedniRecordedPointOrder
