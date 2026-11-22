import FiniteGroupChains

namespace XedniExactChainMultipliers

open XedniRegularChainReduction XedniRegularGroupLaw
open XedniLocalZModReduction XedniRecordedRegularSteps
open XedniCurveEquationCertificates XedniFiniteGroupChains

local instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩
local instance :
    (shortCurve
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) (-1)))
      (reduceZMod 313 ((algebraMap ℤ (localIntegers 313)) 15961))).IsElliptic :=
  row0_reduced_elliptic

inductive RegularChainN {R : Type*} [CommRing R] {A B : R}
    (T : CurvePoint R A B) : ℕ → CurvePoint R A B → CurvePoint R A B → Prop
  | refl (P) : RegularChainN T 0 P P
  | step {n P Q U} (h : RegularStep P T Q)
      (tail : RegularChainN T n Q U) : RegularChainN T (n + 1) P U

theorem reduced_regularChainN_exact {R F : Type*} [CommRing R]
    [Field F] [DecidableEq F] (f : R →+* F) {A B : R}
    [(shortCurve (f A) (f B)).IsElliptic]
    {n : ℕ} {P T Q : CurvePoint R A B}
    (h : RegularChainN T n P Q) :
    toGroupPoint (mapPoint f Q) =
      toGroupPoint (mapPoint f P) + n • toGroupPoint (mapPoint f T) := by
  induction h with
  | refl P => simp
  | step h tail ih =>
      calc
        toGroupPoint (mapPoint f _) =
            toGroupPoint (mapPoint f _) + _ • toGroupPoint (mapPoint f _) := ih
        _ = (toGroupPoint (mapPoint f _) + toGroupPoint (mapPoint f _)) +
              _ • toGroupPoint (mapPoint f _) := by
              rw [← fieldStep_group_add (map_regularStep f h)]
        _ = toGroupPoint (mapPoint f _) + (_ + 1) • toGroupPoint (mapPoint f _) := by
              simp [add_nsmul, add_assoc, add_comm, add_left_comm]

#print axioms reduced_regularChainN_exact

theorem reduced_regularChainN_from_self {R F : Type*} [CommRing R]
    [Field F] [DecidableEq F] (f : R →+* F) {A B : R}
    [(shortCurve (f A) (f B)).IsElliptic]
    {n : ℕ} {T Q : CurvePoint R A B}
    (h : RegularChainN T n T Q) :
    toGroupPoint (mapPoint f Q) = (n + 1) • toGroupPoint (mapPoint f T) := by
  have h' := reduced_regularChainN_exact f h
  simpa only [succ_nsmul, add_comm] using h'

#print axioms reduced_regularChainN_from_self

-- BEGIN GENERATED ROWS
-- Source SHA-256: a34dd1b580483815d7f4dc61877eae9935b16873b8f9bc908b24c2e51a25154e

local instance : Fact (Nat.Prime 421) := ⟨by norm_num⟩
local instance :
    (shortCurve
      (reduceZMod 421 ((algebraMap ℤ (localIntegers 421)) (-1)))
      (reduceZMod 421 ((algebraMap ℤ (localIntegers 421)) (9273786)))).IsElliptic :=
  row1_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 421 ((algebraMap ℤ (localIntegers 421)) (-1)))
      (reduceZMod 421 ((algebraMap ℤ (localIntegers 421)) (8839)))).IsElliptic :=
  row2_reduced_elliptic

local instance : Fact (Nat.Prime 431) := ⟨by norm_num⟩
local instance :
    (shortCurve
      (reduceZMod 431 ((algebraMap ℤ (localIntegers 431)) (-1)))
      (reduceZMod 431 ((algebraMap ℤ (localIntegers 431)) (-402125)))).IsElliptic :=
  row4_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 431 ((algebraMap ℤ (localIntegers 431)) (-1)))
      (reduceZMod 431 ((algebraMap ℤ (localIntegers 431)) (367641)))).IsElliptic :=
  row5_reduced_elliptic

local instance : Fact (Nat.Prime 593) := ⟨by norm_num⟩
local instance :
    (shortCurve
      (reduceZMod 593 ((algebraMap ℤ (localIntegers 593)) (-1)))
      (reduceZMod 593 ((algebraMap ℤ (localIntegers 593)) (-14513084)))).IsElliptic :=
  row6_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 593 ((algebraMap ℤ (localIntegers 593)) (-1)))
      (reduceZMod 593 ((algebraMap ℤ (localIntegers 593)) (11265)))).IsElliptic :=
  row7_reduced_elliptic

local instance : Fact (Nat.Prime 617) := ⟨by norm_num⟩
local instance :
    (shortCurve
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-1)))
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-43809)))).IsElliptic :=
  row8_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-1)))
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-17684456)))).IsElliptic :=
  row9_reduced_elliptic

local instance :
    (shortCurve
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-1)))
      (reduceZMod 617 ((algebraMap ℤ (localIntegers 617)) (-283205)))).IsElliptic :=
  row10_reduced_elliptic

local instance : Fact (Nat.Prime 677) := ⟨by norm_num⟩
local instance :
    (shortCurve
      (reduceZMod 677 ((algebraMap ℤ (localIntegers 677)) (-1)))
      (reduceZMod 677 ((algebraMap ℤ (localIntegers 677)) (-3215075)))).IsElliptic :=
  row11_reduced_elliptic

/-- Row 0: the recorded path has exactly 3 additions. -/
theorem row0_chainN :
    RegularChainN row0_m1_localPoint 3 row0_m1_localPoint row0_m4_localPoint := by
  exact (.step row0_step1 (.step row0_step2 (.step row0_step3 (.refl _))))

theorem row0_exact :
    toGroupPoint (mapPoint (reduceZMod 313) row0_m4_localPoint) =
      4 • toGroupPoint (mapPoint (reduceZMod 313) row0_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 313) row0_chainN

#print axioms row0_chainN
#print axioms row0_exact

/-- Row 1: the recorded path has exactly 4 additions. -/
theorem row1_chainN :
    RegularChainN row1_m1_localPoint 4 row1_m1_localPoint row1_m5_localPoint := by
  exact (.step row1_step1 (.step row1_step2 (.step row1_step3 (.step row1_step4 (.refl _)))))

theorem row1_exact :
    toGroupPoint (mapPoint (reduceZMod 421) row1_m5_localPoint) =
      5 • toGroupPoint (mapPoint (reduceZMod 421) row1_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 421) row1_chainN

#print axioms row1_chainN
#print axioms row1_exact

/-- Row 2: the recorded path has exactly 4 additions. -/
theorem row2_chainN :
    RegularChainN row2_m1_localPoint 4 row2_m1_localPoint row2_m5_localPoint := by
  exact (.step row2_step1 (.step row2_step2 (.step row2_step3 (.step row2_step4 (.refl _)))))

theorem row2_exact :
    toGroupPoint (mapPoint (reduceZMod 421) row2_m5_localPoint) =
      5 • toGroupPoint (mapPoint (reduceZMod 421) row2_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 421) row2_chainN

#print axioms row2_chainN
#print axioms row2_exact

/-- Row 3: the recorded path has exactly 4 additions. -/
theorem row3_chainN :
    RegularChainN row3_m1_localPoint 4 row3_m1_localPoint row3_m5_localPoint := by
  exact (.step row3_step1 (.step row3_step2 (.step row3_step3 (.step row3_step4 (.refl _)))))

theorem row3_exact :
    toGroupPoint (mapPoint (reduceZMod 421) row3_m5_localPoint) =
      5 • toGroupPoint (mapPoint (reduceZMod 421) row3_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 421) row3_chainN

#print axioms row3_chainN
#print axioms row3_exact

/-- Row 4: the recorded path has exactly 5 additions. -/
theorem row4_chainN :
    RegularChainN row4_m1_localPoint 5 row4_m1_localPoint row4_m6_localPoint := by
  exact (.step row4_step1 (.step row4_step2 (.step row4_step3 (.step row4_step4 (.step row4_step5 (.refl _))))))

theorem row4_exact :
    toGroupPoint (mapPoint (reduceZMod 431) row4_m6_localPoint) =
      6 • toGroupPoint (mapPoint (reduceZMod 431) row4_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 431) row4_chainN

#print axioms row4_chainN
#print axioms row4_exact

/-- Row 5: the recorded path has exactly 4 additions. -/
theorem row5_chainN :
    RegularChainN row5_m1_localPoint 4 row5_m1_localPoint row5_m5_localPoint := by
  exact (.step row5_step1 (.step row5_step2 (.step row5_step3 (.step row5_step4 (.refl _)))))

theorem row5_exact :
    toGroupPoint (mapPoint (reduceZMod 431) row5_m5_localPoint) =
      5 • toGroupPoint (mapPoint (reduceZMod 431) row5_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 431) row5_chainN

#print axioms row5_chainN
#print axioms row5_exact

/-- Row 6: the recorded path has exactly 3 additions. -/
theorem row6_chainN :
    RegularChainN row6_m1_localPoint 3 row6_m1_localPoint row6_m4_localPoint := by
  exact (.step row6_step1 (.step row6_step2 (.step row6_step3 (.refl _))))

theorem row6_exact :
    toGroupPoint (mapPoint (reduceZMod 593) row6_m4_localPoint) =
      4 • toGroupPoint (mapPoint (reduceZMod 593) row6_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 593) row6_chainN

#print axioms row6_chainN
#print axioms row6_exact

/-- Row 7: the recorded path has exactly 4 additions. -/
theorem row7_chainN :
    RegularChainN row7_m1_localPoint 4 row7_m1_localPoint row7_m5_localPoint := by
  exact (.step row7_step1 (.step row7_step2 (.step row7_step3 (.step row7_step4 (.refl _)))))

theorem row7_exact :
    toGroupPoint (mapPoint (reduceZMod 593) row7_m5_localPoint) =
      5 • toGroupPoint (mapPoint (reduceZMod 593) row7_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 593) row7_chainN

#print axioms row7_chainN
#print axioms row7_exact

/-- Row 8: the recorded path has exactly 5 additions. -/
theorem row8_chainN :
    RegularChainN row8_m1_localPoint 5 row8_m1_localPoint row8_m6_localPoint := by
  exact (.step row8_step1 (.step row8_step2 (.step row8_step3 (.step row8_step4 (.step row8_step5 (.refl _))))))

theorem row8_exact :
    toGroupPoint (mapPoint (reduceZMod 617) row8_m6_localPoint) =
      6 • toGroupPoint (mapPoint (reduceZMod 617) row8_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 617) row8_chainN

#print axioms row8_chainN
#print axioms row8_exact

/-- Row 9: the recorded path has exactly 4 additions. -/
theorem row9_chainN :
    RegularChainN row9_m1_localPoint 4 row9_m1_localPoint row9_m5_localPoint := by
  exact (.step row9_step1 (.step row9_step2 (.step row9_step3 (.step row9_step4 (.refl _)))))

theorem row9_exact :
    toGroupPoint (mapPoint (reduceZMod 617) row9_m5_localPoint) =
      5 • toGroupPoint (mapPoint (reduceZMod 617) row9_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 617) row9_chainN

#print axioms row9_chainN
#print axioms row9_exact

/-- Row 10: the recorded path has exactly 4 additions. -/
theorem row10_chainN :
    RegularChainN row10_m1_localPoint 4 row10_m1_localPoint row10_m5_localPoint := by
  exact (.step row10_step1 (.step row10_step2 (.step row10_step3 (.step row10_step4 (.refl _)))))

theorem row10_exact :
    toGroupPoint (mapPoint (reduceZMod 617) row10_m5_localPoint) =
      5 • toGroupPoint (mapPoint (reduceZMod 617) row10_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 617) row10_chainN

#print axioms row10_chainN
#print axioms row10_exact

/-- Row 11: the recorded path has exactly 5 additions. -/
theorem row11_chainN :
    RegularChainN row11_m1_localPoint 5 row11_m1_localPoint row11_m6_localPoint := by
  exact (.step row11_step1 (.step row11_step2 (.step row11_step3 (.step row11_step4 (.step row11_step5 (.refl _))))))

theorem row11_exact :
    toGroupPoint (mapPoint (reduceZMod 677) row11_m6_localPoint) =
      6 • toGroupPoint (mapPoint (reduceZMod 677) row11_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 677) row11_chainN

#print axioms row11_chainN
#print axioms row11_exact

/-- Row 12: the recorded path has exactly 5 additions. -/
theorem row12_chainN :
    RegularChainN row12_m1_localPoint 5 row12_m1_localPoint row12_m6_localPoint := by
  exact (.step row12_step1 (.step row12_step2 (.step row12_step3 (.step row12_step4 (.step row12_step5 (.refl _))))))

theorem row12_exact :
    toGroupPoint (mapPoint (reduceZMod 677) row12_m6_localPoint) =
      6 • toGroupPoint (mapPoint (reduceZMod 677) row12_m1_localPoint) := by
  exact reduced_regularChainN_from_self (reduceZMod 677) row12_chainN

#print axioms row12_chainN
#print axioms row12_exact
-- END GENERATED ROWS

end XedniExactChainMultipliers
