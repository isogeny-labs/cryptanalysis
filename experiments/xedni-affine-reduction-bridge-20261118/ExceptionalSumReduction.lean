import RegularSumReduction
import Mathlib.Tactic

/-! Finite affine sums with certified regular steps, identity steps, and exact
inverse cancellation commute with reduction to the residue-field group. -/
namespace XedniExceptionalSumReduction

open XedniRegularChainReduction XedniRegularGroupLaw

/-- The affine inverse on a short-Weierstrass curve. -/
def negCurvePoint {R : Type*} [CommRing R] {A B : R}
    (P : CurvePoint R A B) : CurvePoint R A B :=
  ⟨P.x, -P.y, by simpa using P.onCurve⟩

variable {R F : Type*} [CommRing R] [Field F] [DecidableEq F]
variable (f : R →+* F) {A B : R}
variable [(shortCurve (f A) (f B)).IsElliptic]

private def imagePoint (P : CurvePoint R A B) :
    (shortCurve (f A) (f B)).toAffine.Point :=
  toGroupPoint (mapPoint f P)

/-- Affine negation commutes with coefficient and point reduction. -/
theorem image_neg (P : CurvePoint R A B) :
    imagePoint f (negCurvePoint P) = -imagePoint f P := by
  simp only [imagePoint, toGroupPoint, WeierstrassCurve.Affine.Point.mk]
  rw [WeierstrassCurve.Affine.Point.neg_some]
  simp [mapPoint, negCurvePoint, shortCurve, WeierstrassCurve.Affine.negY]

private def imageOption : Option (CurvePoint R A B) →
    (shortCurve (f A) (f B)).toAffine.Point
  | none => 0
  | some P => imagePoint f P

/-- A certified local addition, including affine exceptions whose result is
the point at infinity. `cancel` requires exact local inverses. -/
inductive CertifiedStep {R : Type*} [CommRing R] {A B : R} :
    Option (CurvePoint R A B) → Option (CurvePoint R A B) →
      Option (CurvePoint R A B) → Prop
  | zero_left (T : Option (CurvePoint R A B)) : CertifiedStep none T T
  | zero_right (P : Option (CurvePoint R A B)) : CertifiedStep P none P
  | regular {P T Q : CurvePoint R A B} (h : RegularStep P T Q) :
      CertifiedStep (some P) (some T) (some Q)
  | cancel (P : CurvePoint R A B) :
      CertifiedStep (some P) (some (negCurvePoint P)) none
  | cancel_left (P : CurvePoint R A B) :
      CertifiedStep (some (negCurvePoint P)) (some P) none

theorem reduce_certifiedStep {P T Q : Option (CurvePoint R A B)}
    (h : CertifiedStep P T Q) :
    imageOption f Q = imageOption f P + imageOption f T := by
  cases h with
  | zero_left T => simp [imageOption]
  | zero_right P => simp [imageOption]
  | regular h =>
      simpa only [imageOption, imagePoint] using fieldStep_group_add (map_regularStep f h)
  | cancel P => simp [imageOption, image_neg]
  | cancel_left P => simp [imageOption, image_neg]

/-- A finite ordered sum whose additions each have a `CertifiedStep`. -/
inductive CertifiedSum {R : Type*} [CommRing R] {A B : R} :
    List (Option (CurvePoint R A B)) → Option (CurvePoint R A B) → Prop
  | single (P : Option (CurvePoint R A B)) : CertifiedSum [P] P
  | snoc {xs : List (Option (CurvePoint R A B))}
      {P T Q : Option (CurvePoint R A B)}
      (prior : CertifiedSum xs P) (step : CertifiedStep P T Q) :
      CertifiedSum (xs ++ [T]) Q

/-- Reduction of a certified finite sum equals the elliptic-group sum of
its individually reduced inputs, including identity and exact inverse cases. -/
theorem reduce_certifiedSum {xs : List (Option (CurvePoint R A B))}
    {Q : Option (CurvePoint R A B)} (h : CertifiedSum xs Q) :
    imageOption f Q = (xs.map (imageOption f)).sum := by
  induction h with
  | single P => simp [imageOption]
  | @snoc xs P T Q prior step ih =>
      calc
        imageOption f Q = imageOption f P + imageOption f T :=
          reduce_certifiedStep f step
        _ = ((xs ++ [T]).map (imageOption f)).sum := by
          rw [ih]
          simp [List.map_append, List.sum_append]

/-- Equal certified local endpoints yield equal residue-field group sums. -/
theorem equal_certifiedSums {xs ys : List (Option (CurvePoint R A B))}
    {P Q : Option (CurvePoint R A B)}
    (hx : CertifiedSum xs P) (hy : CertifiedSum ys Q) (hPQ : P = Q) :
    (xs.map (imageOption f)).sum = (ys.map (imageOption f)).sum := by
  calc
    (xs.map (imageOption f)).sum = imageOption f P := (reduce_certifiedSum f hx).symm
    _ = imageOption f Q := by rw [hPQ]
    _ = (ys.map (imageOption f)).sum := reduce_certifiedSum f hy

#print axioms image_neg
#print axioms reduce_certifiedStep
#print axioms reduce_certifiedSum
#print axioms equal_certifiedSums

end XedniExceptionalSumReduction
