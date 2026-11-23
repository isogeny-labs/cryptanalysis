import Mathlib
/-!
Point-order certificate for the base point in
`experiments/prime-field-auxiliary-ic/snapshot/comparison/field31/auxiliary/public.json`.
The unconditional certificates below use a two-point fiber bound and a prime-order witness.
-/
namespace M31Card

abbrev F := ZMod 2147483647

instance : Fact (Nat.Prime 2147483647) := ⟨by native_decide⟩

def E : WeierstrassCurve.Affine F := ⟨0, 0, 0, 2, 14⟩

def P : E.Point := .some (x := 1) (y := 814455902) (by
  rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
  native_decide)

def atInfinity {W : WeierstrassCurve.Affine F} : W.Point → Bool
  | .zero => true
  | .some _ _ _ => false

private theorem zero_of_infinity {W : WeierstrassCurve.Affine F} (A : W.Point)
    (h : atInfinity A = true) : A = 0 := by
  cases A with
  | zero => rfl
  | some x y cert => contradiction

theorem multiple : (2147505293 : ℕ) • P = 0 := by
  apply zero_of_infinity
  native_decide

theorem order : addOrderOf P = 2147505293 := by
  have d := addOrderOf_dvd_of_nsmul_eq_zero multiple
  rcases (Nat.dvd_prime (by native_decide : Nat.Prime 2147505293)).mp d with h | h
  · have hn : P ≠ 0 := WeierstrassCurve.Affine.Point.some_ne_zero _
    exact (hn (AddMonoid.addOrderOf_eq_one_iff.mp h)).elim
  · exact h

theorem unique_cardinality_in_hasse_interval (N : ℕ) (lower : 2147390967 ≤ N) (upper : N ≤ 2147576329)
    (hd : 2147505293 ∣ N) : N = 2147505293 := by omega

theorem curve_cardinality_of_hasse_bounds
    (lower : 2147390967 ≤ Nat.card E.Point) (upper : Nat.card E.Point ≤ 2147576329) :
    Nat.card E.Point = 2147505293 := by
  apply unique_cardinality_in_hasse_interval _ lower upper
  rw [← order]
  exact addOrderOf_dvd_natCard P

section FiberBound
variable {K : Type*} [Field K] [Fintype K]

private def abscissa {W : WeierstrassCurve.Affine K} : W.Point → Option K
  | .zero => none
  | .some x _ _ => some x

omit [Fintype K] in
private theorem sameAbscissa {W : WeierstrassCurve.Affine K} (A B : W.Point)
    (h : abscissa A = abscissa B) : A = B ∨ A = -B := by
  apply WeierstrassCurve.Affine.Point.xRep_eq_xRep_iff.mp
  cases A <;> cases B <;> simp_all [abscissa]

/-- Two signs and an optional x-coordinate suffice to cover every point. -/
theorem cardBounds (W : WeierstrassCurve.Affine K) :
    0 < Nat.card W.Point ∧ Nat.card W.Point ≤ 2*(Fintype.card K+1) := by
  classical
  let pick : Option K → W.Point := Function.invFun abscissa
  let decode : Option K × Bool → W.Point := fun z =>
    if z.2 then -(pick z.1) else pick z.1
  have surj : Function.Surjective decode := by
    intro A
    have h : abscissa (pick (abscissa A)) = abscissa A :=
      Function.invFun_eq ⟨A, rfl⟩
    rcases sameAbscissa A _ h.symm with e | e
    · exact ⟨(abscissa A, false), e.symm⟩
    · exact ⟨(abscissa A, true), e.symm⟩
  let : Finite W.Point := Finite.of_surjective decode surj
  refine ⟨Nat.card_pos, ?_⟩
  have h := Nat.card_le_card_of_surjective decode surj
  simpa [Nat.card_eq_fintype_card, Nat.mul_comm] using h

end FiberBound

theorem firstCardinality : Nat.card E.Point = 2147505293 := by
  obtain ⟨hpos, hmax⟩ := cardBounds E
  rw [show Fintype.card F = 2147483647 from ZMod.card _] at hmax
  have hd := addOrderOf_dvd_natCard P
  rw [order] at hd
  omega

def secondCurve : WeierstrassCurve.Affine F := ⟨0, 0, 0, 2, 36⟩

def secondPoint : secondCurve.Point := .some (x := 0) (y := 6) (by
  rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
  native_decide)

theorem secondPointOrder : addOrderOf secondPoint = 2147506201 := by
  have vanishes : (2147506201 : ℕ) • secondPoint = 0 := by
    apply zero_of_infinity
    native_decide
  rcases (Nat.dvd_prime (by native_decide : Nat.Prime 2147506201)).mp
    (addOrderOf_dvd_of_nsmul_eq_zero vanishes) with h | h
  · exact (WeierstrassCurve.Affine.Point.some_ne_zero _
      (AddMonoid.addOrderOf_eq_one_iff.mp h)).elim
  · exact h

theorem secondCardinality : Nat.card secondCurve.Point = 2147506201 := by
  obtain ⟨hpos, hmax⟩ := cardBounds secondCurve
  rw [show Fintype.card F = 2147483647 from ZMod.card _] at hmax
  have hd := addOrderOf_dvd_natCard secondPoint
  rw [secondPointOrder] at hd
  omega

def shortCurve (b : F) : WeierstrassCurve.Affine F := ⟨0,0,0,2,b⟩
def cubic (b x : F) := x^3 + 2*x + b

private theorem shortEquation (b x y : F) :
    (shortCurve b).Equation x y ↔ y^2 = cubic b x := by
  simp [WeierstrassCurve.Affine.equation_iff, shortCurve, cubic]

private def fiberEquiv (b : F) (smooth : (shortCurve b).Δ ≠ 0) :
    (shortCurve b).Point ≃ Option ((x : F) × {y : F // y^2 = cubic b x}) where
  toFun
    | .zero => none
    | .some x y h => some ⟨x,y,(shortEquation b x y).mp h.1⟩
  invFun
    | none => .zero
    | some ⟨x,y,h⟩ => .some x y (((shortCurve b).equation_iff_nonsingular_of_Δ_ne_zero smooth).mp
        ((shortEquation b x y).mpr h))
  left_inv P := by cases P <;> rfl
  right_inv z := by rcases z with _ | ⟨x,y,h⟩ <;> rfl

private noncomputable def roots (a : F) := ({y : F | y^2 = a} : Set F).toFinset.card

private theorem countShort (b : F) (smooth : (shortCurve b).Δ ≠ 0) :
    Nat.card (shortCurve b).Point = (∑ x : F, roots (cubic b x)) + 1 := by
  classical
  rw [Nat.card_congr (fiberEquiv b smooth)]
  simp [Nat.card_eq_fintype_card, roots, Fintype.card_subtype]

private theorem rootPair (a : F) : roots a + roots (-a) = 2 := by
  have char_ne : ringChar F ≠ 2 := by rw [ZMod.ringChar_zmod_n]; decide
  have minus : quadraticChar F (-1) = -1 := by
    apply (quadraticChar_neg_one char_ne).trans
    rw [show Fintype.card F = 2147483647 from ZMod.card _]
    decide
  have h := quadraticChar_card_sqrts char_ne a
  have negProd {K : Type} [Ring K] (v : K) : (-1 : K)*v = -v := neg_one_mul v
  have c : quadraticChar F (-a) = -quadraticChar F a := calc
    _ = quadraticChar F ((-1)*a) := congrArg _ (negProd a).symm
    _ = quadraticChar F (-1) * quadraticChar F a := map_mul _ _ _
    _ = -quadraticChar F a := by rw [minus]; exact neg_one_mul _
  have j := quadraticChar_card_sqrts char_ne (-a)
  rw [c] at j
  unfold roots
  omega

/-- The -1 twist has coefficients (2,-b). Pair the fibers at x and -x,
including their zero ordinates, and count both points at infinity. -/
theorem twistPair (b : F) (h : (shortCurve b).Δ ≠ 0) (ht : (shortCurve (-b)).Δ ≠ 0) :
    Nat.card (shortCurve b).Point + Nat.card (shortCurve (-b)).Point = 4294967296 := by
  rw [countShort _ h, countShort _ ht]
  have reflect := (Equiv.neg F).sum_comp Finset.univ (fun x => roots (cubic (-b) x)) (by simp)
  simp only [Equiv.neg_apply] at reflect
  have negPoly {K : Type} [CommRing K] (u v : K) :
      (-u)^3 + 2*(-u) + (-v) = -(u^3 + 2*u + v) := by ring
  have replacement : (∑ x : F, roots (cubic (-b) x)) = ∑ x : F, roots (-(cubic b x)) := by
    refine reflect.symm.trans (Finset.sum_congr rfl fun x _ => ?_)
    exact congrArg roots (negPoly x b)
  rw [replacement]
  have pair : (∑ x : F, roots (cubic b x)) + (∑ x : F, roots (-(cubic b x))) =
      2 * Fintype.card F := by
    rw [← Finset.sum_add_distrib]
    simp [rootPair, Nat.mul_comm]
  rw [show Fintype.card F = 2147483647 from ZMod.card _] at pair
  omega

theorem firstTwistCardinality : Nat.card (shortCurve (-14)).Point = 2147462003 := by
  have h := twistPair 14 (by native_decide) (by native_decide)
  change Nat.card E.Point + Nat.card (shortCurve (-14)).Point = _ at h
  rw [firstCardinality] at h
  omega

theorem secondTwistCardinality : Nat.card (shortCurve (-36)).Point = 2147461095 := by
  have h := twistPair 36 (by native_decide) (by native_decide)
  change Nat.card secondCurve.Point + Nat.card (shortCurve (-36)).Point = _ at h
  rw [secondCardinality] at h
  omega

private theorem zeroOfCoprime {G H : Type*} [AddGroup G] [AddGroup H]
    (h : Nat.Coprime (Nat.card G) (Nat.card H)) (f : G →+ H) : f = 0 := by
  ext x
  apply AddMonoid.addOrderOf_eq_one_iff.mp
  exact Nat.dvd_one.mp (h ▸ Nat.dvd_gcd
    ((addOrderOf_map_dvd f x).trans (addOrderOf_dvd_natCard x))
    (addOrderOf_dvd_natCard (f x)))

theorem firstTwistTransfer (f : E.Point →+ (shortCurve (-14)).Point) : f = 0 := by
  apply zeroOfCoprime _ f
  rw [firstCardinality, firstTwistCardinality]
  decide

theorem secondTwistTransfer (f : secondCurve.Point →+ (shortCurve (-36)).Point) : f = 0 := by
  apply zeroOfCoprime _ f
  rw [secondCardinality, secondTwistCardinality]
  decide

/-- A zero ordinate would supply a nonidentity rational point killed by two. -/
theorem noZeroCubic (b : F) (smooth : (shortCurve b).Δ ≠ 0)
    (odd : Odd (Nat.card (shortCurve b).Point)) (x : F) : cubic b x ≠ 0 := by
  intro hx
  have ns : (shortCurve b).Nonsingular x 0 := by
    apply ((shortCurve b).equation_iff_nonsingular_of_Δ_ne_zero smooth).mp
    exact (shortEquation b x 0).mpr (by rw [hx]; simp)
  let A : (shortCurve b).Point := .some x 0 ns
  have twice : (2 : ℕ) • A = 0 := by
    rw [two_nsmul]
    apply WeierstrassCurve.Affine.Point.add_self_of_Y_eq
    simp [WeierstrassCurve.Affine.negY, shortCurve]
    decide
  have hd := Nat.dvd_gcd (addOrderOf_dvd_natCard A)
    (addOrderOf_dvd_iff_nsmul_eq_zero.mpr twice)
  rw [odd.coprime_two_right.gcd_eq_one] at hd
  exact WeierstrassCurve.Affine.Point.some_ne_zero ns
    (AddMonoid.addOrderOf_eq_one_iff.mp (Nat.dvd_one.mp hd))

noncomputable def liftCount (b : F) : ℕ := by
  classical
  exact (Finset.univ.filter (fun x : F => IsSquare (cubic b x))).card

theorem orderFromLiftCount (b : F) (smooth : (shortCurve b).Δ ≠ 0)
    (odd : Odd (Nat.card (shortCurve b).Point)) :
    Nat.card (shortCurve b).Point = 2*liftCount b + 1 := by
  classical
  have char_ne : ringChar F ≠ 2 := by rw [ZMod.ringChar_zmod_n]; decide
  have fibers (x : F) : roots (cubic b x) = if IsSquare (cubic b x) then 2 else 0 := by
    have h := quadraticChar_card_sqrts char_ne (cubic b x)
    unfold roots
    split <;> rename_i hs
    · rw [(quadraticChar_one_iff_isSquare (noZeroCubic b smooth odd x)).mpr hs] at h
      omega
    · rw [quadraticChar_neg_one_iff_not_isSquare.mpr hs] at h
      omega
  rw [countShort b smooth]
  simp_rw [fibers]
  simp only [Nat.add_left_inj, ← Finset.sum_filter]
  simp [liftCount, Nat.mul_comm]

theorem fixtureLiftCounts : liftCount 14 = 1073752646 ∧ liftCount 36 = 1073753100 := by
  have first : Nat.card (shortCurve 14).Point = 2147505293 := firstCardinality
  have second : Nat.card (shortCurve 36).Point = 2147506201 := secondCardinality
  have a := orderFromLiftCount 14 (by native_decide) (by rw [first]; decide)
  have b := orderFromLiftCount 36 (by native_decide) (by rw [second]; decide)
  omega

end M31Card
