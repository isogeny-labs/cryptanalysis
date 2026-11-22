import CertifiedRelationExtraction
import FiniteGroupChains
import Mathlib.Tactic

/-! A recorded four-step xedni path supplies the concrete finite-sum
certificate required by the pathwise public-relation theorem. -/

namespace XedniRecordedCertifiedRelation

open XedniRegularChainReduction XedniRegularGroupLaw
open XedniExceptionalSumReduction XedniCertifiedRelationExtraction
open XedniLocalZModReduction XedniCurveEquationCertificates
open XedniRecordedRegularSteps XedniFiniteGroupChains

local instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩

local instance :
    (shortCurve
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) (-1)))
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) (15961)))).IsElliptic := by
  simpa [reduce_integer, map_ofNat] using row0_elliptic

/-- Three certified regular additions build `4T`, then exact inverse
cancellation gives the point at infinity. -/
theorem row0_certified_sum :
    CertifiedSum
      [some row0_m1_localPoint, some row0_m1_localPoint,
       some row0_m1_localPoint, some row0_m1_localPoint,
       some (negCurvePoint row0_m4_localPoint)] none := by
  have h1 : CertifiedSum [some row0_m1_localPoint]
      (some row0_m1_localPoint) := .single _
  have h2 : CertifiedSum [some row0_m1_localPoint, some row0_m1_localPoint]
      (some row0_m2_localPoint) := by
    simpa using CertifiedSum.snoc h1 (CertifiedStep.regular row0_step1)
  have h3 : CertifiedSum
      [some row0_m1_localPoint, some row0_m1_localPoint,
       some row0_m1_localPoint] (some row0_m3_localPoint) := by
    simpa using CertifiedSum.snoc h2 (CertifiedStep.regular row0_step2)
  have h4 : CertifiedSum
      [some row0_m1_localPoint, some row0_m1_localPoint,
       some row0_m1_localPoint, some row0_m1_localPoint]
      (some row0_m4_localPoint) := by
    simpa using CertifiedSum.snoc h3 (CertifiedStep.regular row0_step3)
  simpa using CertifiedSum.snoc h4 (CertifiedStep.cancel row0_m4_localPoint)

/-- The recorded local certificate gives `4P - T = 0` after reduction. -/
theorem row0_public_relation_from_certified_sum :
    (4 : ℤ) • toGroupPoint (mapPoint (reduceZMod 313) row0_m1_localPoint) -
      toGroupPoint (mapPoint (reduceZMod 313) row0_m4_localPoint) = 0 := by
  have h := certified_sum_public_relation 313 (reduceZMod 313)
    row0_m1_localPoint row0_m4_localPoint false true 4 1
    (show CertifiedSum
      (List.replicate 4 (some row0_m1_localPoint) ++
        List.replicate 1 (some (negCurvePoint row0_m4_localPoint))) none from
      row0_certified_sum)
  simpa [signedCoefficient, publicImage, sub_eq_add_neg] using h

#print axioms row0_certified_sum
#print axioms row0_public_relation_from_certified_sum

end XedniRecordedCertifiedRelation
