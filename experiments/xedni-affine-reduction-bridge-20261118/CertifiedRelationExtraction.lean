import ExceptionalSumReduction
import AdaptivePublicRelationReduction
import Mathlib.Tactic

/-! A certified finite local addition path ending at infinity yields a
public relation and, when its target coefficient is invertible, an exact
scalar certificate. This uses stepwise reduction rather than a global
homomorphism on all rational points. -/

namespace XedniCertifiedRelationExtraction

open XedniRegularChainReduction XedniRegularGroupLaw
open XedniExceptionalSumReduction
open XedniAdaptivePublicRelationReduction

variable {R : Type*} [CommRing R]
variable (q : ℕ) [Fact (Nat.Prime q)]
variable (f : R →+* ZMod q) {A B : R}
variable [(shortCurve (f A) (f B)).IsElliptic]

private def publicImage (P : CurvePoint R A B) :
    (shortCurve (f A) (f B)).toAffine.Point :=
  toGroupPoint (mapPoint f P)

private def signedPoint (negative : Bool) (P : CurvePoint R A B) :
    Option (CurvePoint R A B) :=
  some (if negative then negCurvePoint P else P)

private def signedCoefficient (negative : Bool) (n : ℕ) : ℤ :=
  if negative then -(n : ℤ) else n

private theorem publicImage_neg (P : CurvePoint R A B) :
    publicImage q f (negCurvePoint P) = -publicImage q f P := by
  have h := image_neg f P
  change publicImage q f (negCurvePoint P) = -publicImage q f P at h
  exact h

private theorem signed_replicate_sum (negative : Bool) (n : ℕ)
    (P : CurvePoint R A B) :
    ((List.replicate n (signedPoint negative P)).map
      (fun X => match X with
        | none => (0 : (shortCurve (f A) (f B)).toAffine.Point)
        | some Y => publicImage q f Y)).sum =
      signedCoefficient negative n • publicImage q f P := by
  cases negative <;>
    simp [signedPoint, signedCoefficient, publicImage_neg,
      List.map_replicate, List.sum_replicate]

/-- A certified local path with signed repeated inputs and endpoint at
infinity yields the corresponding public integer relation. -/
theorem certified_sum_public_relation (p t : CurvePoint R A B)
    (sa sb : Bool) (m n : ℕ)
    (hcert : CertifiedSum
      (List.replicate m (signedPoint sa p) ++
        List.replicate n (signedPoint sb t)) none) :
    signedCoefficient sa m • publicImage q f p +
      signedCoefficient sb n • publicImage q f t = 0 := by
  have h := reduce_certifiedSum f hcert
  change (0 : (shortCurve (f A) (f B)).toAffine.Point) =
    ((List.replicate m (signedPoint sa p) ++
      List.replicate n (signedPoint sb t)).map
      (fun X => match X with
        | none => (0 : (shortCurve (f A) (f B)).toAffine.Point)
        | some Y => publicImage q f Y)).sum at h
  rw [List.map_append, List.sum_append,
    signed_replicate_sum q f sa m p, signed_replicate_sum q f sb n t] at h
  exact h.symm

/-- A certified selected local path supplies the exact public target
scalar residue under the explicit base-order and subgroup conditions. -/
theorem certified_sum_recovers_scalar (p t : CurvePoint R A B)
    (sa sb : Bool) (m n : ℕ)
    (hcert : CertifiedSum
      (List.replicate m (signedPoint sa p) ++
        List.replicate n (signedPoint sb t)) none)
    (horder : addOrderOf (publicImage q f p) = q)
    (hsub : publicImage q f t ∈ AddSubgroup.zmultiples (publicImage q f p))
    (hb : (signedCoefficient sb n : ZMod q) ≠ 0) :
    ∃ v : ℤ, publicImage q f t = v • publicImage q f p ∧
      (v : ZMod q) =
        -(signedCoefficient sa m : ZMod q) /
          (signedCoefficient sb n : ZMod q) := by
  exact integer_relation_for_subgroup q (publicImage q f p) (publicImage q f t)
    horder hsub (signedCoefficient sa m) (signedCoefficient sb n) hb
    (certified_sum_public_relation q f p t sa sb m n hcert)

#print axioms certified_sum_public_relation
#print axioms certified_sum_recovers_scalar

end XedniCertifiedRelationExtraction
