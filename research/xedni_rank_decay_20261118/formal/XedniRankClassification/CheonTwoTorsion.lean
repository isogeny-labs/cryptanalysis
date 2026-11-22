import Init.Data.Int.Basic
import Init.Data.Int.Lemmas
import Init.GrindInstances.Ring.Int
import Std.Tactic

/-
The formal result isolates the new boundary used by the two-torsion audit.
The Python verifier separately replays the complete published discriminant
factorization.  Writing the common base and the gap explicitly avoids hiding
the construction's two nonunit factors in expanded polynomial syntax.
-/

namespace XedniRankDecay.CheonTwoTorsion

def two : Int := Int.ofNat 2
def four : Int := Int.ofNat 4

def gap (p t1 t2 s1 n : Int) : Int :=
  Int.add (Int.mul (Int.mul t1 p) n)
    (Int.mul s1 (Int.add (Int.mul t1 t1) (Int.mul t2 t2)))

def factorPlus (base p t1 t2 s1 n : Int) : Int :=
  Int.add base (Int.mul two (gap p t1 t2 s1 n))

def factorMinus (base p t1 t2 s1 n : Int) : Int :=
  Int.sub base (Int.mul two (gap p t1 t2 s1 n))

def firstOrdinate (p t1 t2 s1 n : Int) : Int :=
  Int.mul t1 (gap p t1 t2 s1 n)

theorem factor_difference (base p t1 t2 s1 n : Int) :
    Int.sub (factorPlus base p t1 t2 s1 n)
      (factorMinus base p t1 t2 s1 n) =
      Int.mul four (gap p t1 t2 s1 n) := by
  simp only [factorPlus, factorMinus, two, four]
  grind

theorem factor_difference_binds_first_ordinate
    (base p t1 t2 s1 n : Int) :
    Int.mul t1
      (Int.sub (factorPlus base p t1 t2 s1 n)
        (factorMinus base p t1 t2 s1 n)) =
      Int.mul four (firstOrdinate p t1 t2 s1 n) := by
  rw [factor_difference]
  simp only [firstOrdinate, four]
  grind

theorem nonzero_first_ordinate_implies_distinct_factors
    {base p t1 t2 s1 n : Int}
    (h : firstOrdinate p t1 t2 s1 n ≠ Int.ofNat 0) :
    factorPlus base p t1 t2 s1 n ≠
      factorMinus base p t1 t2 s1 n := by
  intro equalFactors
  have bound :=
    factor_difference_binds_first_ordinate base p t1 t2 s1 n
  rw [equalFactors] at bound
  simp only [four] at bound
  exact h (by grind)

end XedniRankDecay.CheonTwoTorsion

#print axioms XedniRankDecay.CheonTwoTorsion.factor_difference
#print axioms XedniRankDecay.CheonTwoTorsion.factor_difference_binds_first_ordinate
#print axioms XedniRankDecay.CheonTwoTorsion.nonzero_first_ordinate_implies_distinct_factors
