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
variable (fieldPrime : ℕ) [Fact (Nat.Prime fieldPrime)]
variable (f : R →+* ZMod fieldPrime) {A B : R}
variable [(shortCurve (f A) (f B)).IsElliptic]

def publicImage (P : CurvePoint R A B) :
    (shortCurve (f A) (f B)).toAffine.Point :=
  toGroupPoint (mapPoint f P)

def signedPoint (negative : Bool) (P : CurvePoint R A B) :
    Option (CurvePoint R A B) :=
  some (if negative then negCurvePoint P else P)

def signedCoefficient (negative : Bool) (n : ℕ) : ℤ :=
  if negative then -(n : ℤ) else n

private theorem publicImage_neg (P : CurvePoint R A B) :
    publicImage fieldPrime f (negCurvePoint P) = -publicImage fieldPrime f P := by
  have h := image_neg f P
  change publicImage fieldPrime f (negCurvePoint P) = -publicImage fieldPrime f P at h
  exact h

private theorem signed_replicate_sum (negative : Bool) (n : ℕ)
    (P : CurvePoint R A B) :
    ((List.replicate n (signedPoint negative P)).map
      (fun X => match X with
        | none => (0 : (shortCurve (f A) (f B)).toAffine.Point)
        | some Y => publicImage fieldPrime f Y)).sum =
      signedCoefficient negative n • publicImage fieldPrime f P := by
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
    signedCoefficient sa m • publicImage fieldPrime f p +
      signedCoefficient sb n • publicImage fieldPrime f t = 0 := by
  have h := reduce_certifiedSum f hcert
  change (0 : (shortCurve (f A) (f B)).toAffine.Point) =
    ((List.replicate m (signedPoint sa p) ++
      List.replicate n (signedPoint sb t)).map
      (fun X => match X with
        | none => (0 : (shortCurve (f A) (f B)).toAffine.Point)
        | some Y => publicImage fieldPrime f Y)).sum at h
  rw [List.map_append, List.sum_append,
    signed_replicate_sum fieldPrime f sa m p, signed_replicate_sum fieldPrime f sb n t] at h
  exact h.symm

/-- A certified selected local path supplies the exact public target
scalar residue under the explicit base-order and subgroup conditions. -/
theorem certified_sum_recovers_scalar (r : ℕ) [Fact (Nat.Prime r)]
    (p t : CurvePoint R A B)
    (sa sb : Bool) (m n : ℕ)
    (hcert : CertifiedSum
      (List.replicate m (signedPoint sa p) ++
        List.replicate n (signedPoint sb t)) none)
    (horder : addOrderOf (publicImage fieldPrime f p) = r)
    (hsub : publicImage fieldPrime f t ∈ AddSubgroup.zmultiples (publicImage fieldPrime f p))
    (hb : (signedCoefficient sb n : ZMod r) ≠ 0) :
    ∃ v : ℤ, publicImage fieldPrime f t = v • publicImage fieldPrime f p ∧
      (v : ZMod r) =
        -(signedCoefficient sa m : ZMod r) /
          (signedCoefficient sb n : ZMod r) := by
  exact integer_relation_for_subgroup r (publicImage fieldPrime f p) (publicImage fieldPrime f t)
    horder hsub (signedCoefficient sa m) (signedCoefficient sb n) hb
    (certified_sum_public_relation fieldPrime f p t sa sb m n hcert)

#print axioms certified_sum_public_relation
#print axioms certified_sum_recovers_scalar

end XedniCertifiedRelationExtraction
