import RationalLocalWitness
import Mathlib.RingTheory.Localization.FractionRing

/-!
The integer localization at `(p)` embeds in `ℚ`. This embedding identifies the
local representative of an admissible rational coordinate with its rational
value, allowing a rational short-Weierstrass equation to be transported back
to a prime-local curve point.
-/

namespace XedniRationalCurveBridge

open XedniLocalZModReduction XedniRationalLocalWitness
open XedniRegularChainReduction

variable (p : ℕ) [Fact (Nat.Prime p)]

local instance : (primeIdeal p).IsMaximal := Int.ideal_span_isMaximal_of_prime p
local instance : (primeIdeal p).IsPrime := inferInstance

private theorem denominator_unit_rat (s : (primeIdeal p).primeCompl) :
    IsUnit ((s : ℤ) : ℚ) := by
  have hs : (s : ℤ) ≠ 0 := by
    intro hz
    exact s.property (by simpa [hz] using (primeIdeal p).zero_mem)
  exact isUnit_iff_ne_zero.mpr (by exact_mod_cast hs)

/-- The canonical embedding of the prime-local integers into `ℚ`. -/
noncomputable def localToRat : localIntegers p →+* ℚ :=
  IsLocalization.lift (g := Int.castRingHom ℚ) (denominator_unit_rat p)

theorem localToRat_integer (z : ℤ) :
    localToRat p ((algebraMap ℤ (localIntegers p)) z) = (z : ℚ) := by
  exact IsLocalization.lift_eq (denominator_unit_rat p) z

theorem localToRat_fraction (q : ℚ) (h : Admissible p q) :
    localToRat p (toLocal p q h) = q := by
  let s : (primeIdeal p).primeCompl := ⟨(q.den : ℤ), h⟩
  have hmk : toLocal p q h = IsLocalization.mk' (localIntegers p) q.num s := rfl
  rw [hmk]
  change IsLocalization.lift (g := Int.castRingHom ℚ) (denominator_unit_rat p)
    (IsLocalization.mk' (localIntegers p) q.num s) = q
  apply (IsLocalization.lift_mk'_spec (g := Int.castRingHom ℚ)
    (hg := denominator_unit_rat p) q.num q s).2
  have hden : (q.den : ℚ) ≠ 0 := by exact_mod_cast q.den_ne_zero
  simpa [s, Int.cast_natCast, mul_comm] using
    (div_eq_iff hden).mp (rational_reconstruction q)

theorem localToRat_injective : Function.Injective (localToRat p) := by
  apply IsLocalization.injective_of_map_algebraMap_zero
    (M := (primeIdeal p).primeCompl)
  intro z hz
  have hrat : (z : ℚ) = 0 := by simpa only [localToRat_integer] using hz
  have hint : z = 0 := by exact_mod_cast hrat
  simp [hint]

/-- A rational short-Weierstrass equation gives a curve point over the
localization when both coordinates have admissible denominators. -/
noncomputable def localCurvePoint (A B : ℤ) (x y : ℚ)
    (hx : Admissible p x) (hy : Admissible p y)
    (hcurve : y ^ 2 = x ^ 3 + (A : ℚ) * x + B) :
    CurvePoint (localIntegers p)
      ((algebraMap ℤ (localIntegers p)) A)
      ((algebraMap ℤ (localIntegers p)) B) := by
  refine ⟨toLocal p x hx, toLocal p y hy, ?_⟩
  apply localToRat_injective p
  simpa only [map_pow, map_add, map_mul, localToRat_fraction,
    localToRat_integer] using hcurve

#print axioms localToRat_integer
#print axioms localToRat_fraction
#print axioms localToRat_injective
#print axioms localCurvePoint

end XedniRationalCurveBridge
