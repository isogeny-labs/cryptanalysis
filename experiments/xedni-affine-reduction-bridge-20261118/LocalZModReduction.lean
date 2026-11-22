import PrimeLocalReduction
import Mathlib.RingTheory.Ideal.Int
import Mathlib.Data.ZMod.QuotientRing

/-!
The integer-prime specialization of prime-local reduction, with codomain
`ZMod p` rather than an abstract residue field.
-/

namespace XedniLocalZModReduction

open XedniPrimeLocalReduction

abbrev primeIdeal (p : ℕ) : Ideal ℤ := Ideal.span {(p : ℤ)}

variable (p : ℕ) [Fact (Nat.Prime p)]

local instance : (primeIdeal p).IsMaximal := Int.ideal_span_isMaximal_of_prime p
local instance : (primeIdeal p).IsPrime := inferInstance
attribute [local instance] Ideal.Quotient.field

abbrev localIntegers := localRing (primeIdeal p)

noncomputable def reduceZMod : localIntegers p →+* ZMod p :=
  (Int.quotientSpanNatEquivZMod p).toRingHom.comp
    ((quotientEquivResidue (primeIdeal p)).symm.toRingHom.comp
      (reduce (primeIdeal p)))

theorem reduce_integer (z : ℤ) :
    reduceZMod p ((algebraMap ℤ (localIntegers p)) z) = (z : ZMod p) := by
  change (Int.quotientSpanNatEquivZMod p)
    ((quotientEquivResidue (primeIdeal p)).symm
      (reduce (primeIdeal p) ((algebraMap ℤ (localIntegers p)) z))) = (z : ZMod p)
  rw [← integer_reduction (primeIdeal p) z]
  simp only [RingEquiv.symm_apply_apply]
  exact congrArg (fun f : ℤ →+* ZMod p => f z)
    (Int.quotientSpanNatEquivZMod_comp_Quotient_mk p)

theorem reduce_fraction (z : ℤ) (s : (primeIdeal p).primeCompl) :
    reduceZMod p (IsLocalization.mk' (localIntegers p) z s) =
      (z : ZMod p) / ((s : ℤ) : ZMod p) := by
  change (Int.quotientSpanNatEquivZMod p)
    ((quotientEquivResidue (primeIdeal p)).symm
      (reduce (primeIdeal p) (IsLocalization.mk' (localIntegers p) z s))) =
        (z : ZMod p) / ((s : ℤ) : ZMod p)
  rw [fraction_reduction (primeIdeal p) z s]
  rw [map_mul, map_inv₀]
  have hz : (Int.quotientSpanNatEquivZMod p) (Ideal.Quotient.mk (primeIdeal p) z) =
      (z : ZMod p) := by
    simpa [primeIdeal] using
      congrArg (fun f : ℤ →+* ZMod p => f z)
        (Int.quotientSpanNatEquivZMod_comp_Quotient_mk p)
  have hs : (Int.quotientSpanNatEquivZMod p)
      (Ideal.Quotient.mk (primeIdeal p) (s : ℤ)) = ((s : ℤ) : ZMod p) := by
    simpa [primeIdeal] using
      congrArg (fun f : ℤ →+* ZMod p => f (s : ℤ))
        (Int.quotientSpanNatEquivZMod_comp_Quotient_mk p)
  rw [hz, hs, div_eq_mul_inv]

#print axioms reduce_integer
#print axioms reduce_fraction

end XedniLocalZModReduction
