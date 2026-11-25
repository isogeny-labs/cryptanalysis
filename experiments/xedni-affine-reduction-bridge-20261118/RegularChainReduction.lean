import AffineReductionBridge

/-!
A finite path of regular affine additions transfers through a ring homomorphism
to a field. Points carry their short-Weierstrass curve equation, and every
source step carries its chord or tangent formula with a unit denominator.
-/

namespace XedniRegularChainReduction

open XedniAffineReductionBridge

structure CurvePoint (R : Type*) [CommRing R] (A B : R) where
  x : R
  y : R
  onCurve : y ^ 2 = x ^ 3 + A * x + B

variable {R S : Type*} [CommRing R] [Field S]

def mapPoint (f : R →+* S) {A B : R} (P : CurvePoint R A B) :
    CurvePoint S (f A) (f B) :=
  ⟨f P.x, f P.y, by
    have h := congrArg f P.onCurve
    simpa only [map_pow, map_add, map_mul] using h⟩

def RegularStep {A B : R} (P T Q : CurvePoint R A B) : Prop :=
  (∃ d : Rˣ, (d : R) = T.x - P.x ∧
      Q.x = addX P.x T.x (regularSlope (T.y - P.y) d) ∧
      Q.y = addY P.x P.y Q.x (regularSlope (T.y - P.y) d)) ∨
  (P = T ∧ ∃ d : Rˣ, (d : R) = 2 * P.y ∧
      Q.x = addX P.x P.x (regularSlope (3 * P.x ^ 2 + A) d) ∧
      Q.y = addY P.x P.y Q.x (regularSlope (3 * P.x ^ 2 + A) d))

def FieldStep {A B : S} (P T Q : CurvePoint S A B) : Prop :=
  (T.x - P.x ≠ 0 ∧
      Q.x = addX P.x T.x ((T.y - P.y) / (T.x - P.x)) ∧
      Q.y = addY P.x P.y Q.x ((T.y - P.y) / (T.x - P.x))) ∨
  (P = T ∧ 2 * P.y ≠ 0 ∧
      Q.x = addX P.x P.x ((3 * P.x ^ 2 + A) / (2 * P.y)) ∧
      Q.y = addY P.x P.y Q.x ((3 * P.x ^ 2 + A) / (2 * P.y)))

private theorem map_unit_ne_zero (f : R →+* S) (d : Rˣ) : f (d : R) ≠ 0 := by
  intro hzero
  have hmul : f (d : R) * f ((d⁻¹ : Rˣ) : R) = 1 := by
    rw [← map_mul]
    simp
  simp [hzero] at hmul

theorem map_regularStep (f : R →+* S) {A B : R}
    {P T Q : CurvePoint R A B} (h : RegularStep P T Q) :
    FieldStep (mapPoint f P) (mapPoint f T) (mapPoint f Q) := by
  rcases h with ⟨d, hd, hx, hy⟩ | ⟨hPT, d, hd, hx, hy⟩
  · left
    have hmap := regular_chord_reduction f P.x P.y T.x T.y d hd
    dsimp only [mapPoint, FieldStep, CurvePoint.x, CurvePoint.y] at *
    refine ⟨?_, ?_, ?_⟩
    · simpa only [← map_sub, ← hd] using map_unit_ne_zero f d
    · calc
        f Q.x = f (addX P.x T.x (regularSlope (T.y - P.y) d)) := congrArg f hx
        _ = addX (f P.x) (f T.x) (f (regularSlope (T.y - P.y) d)) :=
          map_addX f P.x T.x _
        _ = _ := by rw [hmap.1]
    · calc
        f Q.y = f (addY P.x P.y Q.x (regularSlope (T.y - P.y) d)) := congrArg f hy
        _ = addY (f P.x) (f P.y) (f Q.x) (f (regularSlope (T.y - P.y) d)) :=
          map_addY f P.x P.y Q.x _
        _ = _ := by rw [hmap.1]
  · right
    have hmap := regular_tangent_reduction f A P.x P.y d hd
    dsimp only [mapPoint, FieldStep, CurvePoint.x, CurvePoint.y] at *
    refine ⟨congrArg (mapPoint f) hPT, ?_, ?_, ?_⟩
    · have hden : f (d : R) = 2 * f P.y := by rw [hd, map_mul, map_ofNat]
      exact hden ▸ map_unit_ne_zero f d
    · calc
        f Q.x = f (addX P.x P.x (regularSlope (3 * P.x ^ 2 + A) d)) := congrArg f hx
        _ = addX (f P.x) (f P.x) (f (regularSlope (3 * P.x ^ 2 + A) d)) :=
          map_addX f P.x P.x _
        _ = _ := by rw [hmap.1]
    · calc
        f Q.y = f (addY P.x P.y Q.x (regularSlope (3 * P.x ^ 2 + A) d)) := congrArg f hy
        _ = addY (f P.x) (f P.y) (f Q.x) (f (regularSlope (3 * P.x ^ 2 + A) d)) :=
          map_addY f P.x P.y Q.x _
        _ = _ := by rw [hmap.1]

inductive RegularChain {A B : R} (T : CurvePoint R A B) :
    CurvePoint R A B → CurvePoint R A B → Prop
  | refl (P) : RegularChain T P P
  | step {P Q U} (h : RegularStep P T Q) (tail : RegularChain T Q U) :
      RegularChain T P U

inductive FieldChain {A B : S} (T : CurvePoint S A B) :
    CurvePoint S A B → CurvePoint S A B → Prop
  | refl (P) : FieldChain T P P
  | step {P Q U} (h : FieldStep P T Q) (tail : FieldChain T Q U) :
      FieldChain T P U

theorem map_regularChain (f : R →+* S) {A B : R}
    {P T Q : CurvePoint R A B} (h : RegularChain T P Q) :
    FieldChain (mapPoint f T) (mapPoint f P) (mapPoint f Q) := by
  induction h with
  | refl P => exact .refl _
  | step h tail ih => exact .step (map_regularStep f h) ih

#print axioms mapPoint
#print axioms map_regularStep
#print axioms map_regularChain

end XedniRegularChainReduction
