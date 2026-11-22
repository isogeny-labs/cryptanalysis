import RegularGroupLaw
import Mathlib.Tactic

/-! Arbitrary finite sums built from affine additions with unit denominators
commute with reduction to the elliptic group over a residue field. -/
namespace XedniRegularSumReduction

open XedniRegularChainReduction XedniRegularGroupLaw

/-- A certificate for an ordered finite sum of local curve points. Every
addition carries the unit-denominator `RegularStep` proof. -/
inductive RegularSum {R : Type*} [CommRing R] {A B : R} :
    List (CurvePoint R A B) → CurvePoint R A B → Prop
  | single (P : CurvePoint R A B) : RegularSum [P] P
  | snoc {xs : List (CurvePoint R A B)} {P T Q : CurvePoint R A B}
      (prior : RegularSum xs P) (step : RegularStep P T Q) :
      RegularSum (xs ++ [T]) Q

variable {R F : Type*} [CommRing R] [Field F] [DecidableEq F]
variable (f : R →+* F) {A B : R}
variable [(shortCurve (f A) (f B)).IsElliptic]

private def imagePoint (P : CurvePoint R A B) :
    (shortCurve (f A) (f B)).toAffine.Point :=
  toGroupPoint (mapPoint f P)

/-- A fully regular affine sum has the same value after coefficient and point
reduction as the sum of its individually reduced inputs. -/
theorem reduce_regularSum {xs : List (CurvePoint R A B)}
    {Q : CurvePoint R A B} (h : RegularSum xs Q) :
    imagePoint f Q = (xs.map (imagePoint f)).sum := by
  induction h with
  | single P => simp [imagePoint]
  | @snoc xs P T Q prior step ih =>
      calc
        imagePoint f Q = imagePoint f P + imagePoint f T :=
          fieldStep_group_add (map_regularStep f step)
        _ = ((xs ++ [T]).map (imagePoint f)).sum := by
          rw [ih]
          simp [List.map_append, List.sum_append]

/-- Equal local endpoints of two certified regular sums imply equal sums of
their reduced point lists. -/
theorem equal_regularSums {xs ys : List (CurvePoint R A B)}
    {P Q : CurvePoint R A B}
    (hx : RegularSum xs P) (hy : RegularSum ys Q) (hPQ : P = Q) :
    (xs.map (imagePoint f)).sum = (ys.map (imagePoint f)).sum := by
  calc
    (xs.map (imagePoint f)).sum = imagePoint f P := (reduce_regularSum f hx).symm
    _ = imagePoint f Q := by rw [hPQ]
    _ = (ys.map (imagePoint f)).sum := reduce_regularSum f hy

#print axioms reduce_regularSum
#print axioms equal_regularSums

end XedniRegularSumReduction
