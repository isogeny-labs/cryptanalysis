import LocalZModReduction
import Mathlib.Data.Rat.Lemmas

/-!
A rational coordinate whose canonical denominator lies outside `(p)` has a
specified representative in the localization of `ℤ` at `(p)`. Its reduction is
the expected quotient in `ZMod p`.
-/

namespace XedniRationalLocalWitness

open XedniLocalZModReduction

variable (p : ℕ) [Fact (Nat.Prime p)]

/-- The canonical rational denominator is invertible at the prime `p`. -/
def Admissible (q : ℚ) : Prop := (q.den : ℤ) ∉ primeIdeal p

/-- Admissibility can be checked by integer divisibility of the canonical
denominator. -/
theorem admissible_iff_not_dvd (q : ℚ) :
    Admissible p q ↔ ¬ (p : ℤ) ∣ (q.den : ℤ) := by
  simp [Admissible, primeIdeal, Ideal.mem_span_singleton]

private def denominator (q : ℚ) (h : Admissible p q) :
    (primeIdeal p).primeCompl := ⟨(q.den : ℤ), h⟩

/-- Realize a rational coordinate with admissible denominator in `ℤ_(p)`. -/
noncomputable def toLocal (q : ℚ) (h : Admissible p q) : localIntegers p :=
  IsLocalization.mk' (localIntegers p) q.num (denominator p q h)

/-- The rational value represented by the numerator and denominator is `q`. -/
theorem rational_reconstruction (q : ℚ) :
    (q.num : ℚ) / (q.den : ℚ) = q := by
  exact q.num_div_den

/-- Reduction of an admissible rational coordinate uses its canonical
numerator and denominator. -/
theorem reduce_rational (q : ℚ) (h : Admissible p q) :
    reduceZMod p (toLocal p q h) =
      (q.num : ZMod p) / (q.den : ZMod p) := by
  simpa only [toLocal, denominator, Subtype.coe_mk, Int.cast_natCast] using
    reduce_fraction p q.num (denominator p q h)

#print axioms admissible_iff_not_dvd
#print axioms rational_reconstruction
#print axioms reduce_rational

end XedniRationalLocalWitness
