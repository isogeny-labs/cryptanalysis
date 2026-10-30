module

public import Mathlib.Tactic.FinCases
public import Mathlib.Data.Fintype.Fin

/-! Exact pointwise integer certificate for the frozen D=-7, f=14 class. -/
namespace MixedDegreeWitness

public def sparse (xs : List (Nat × Int)) (i : Fin 32) : Int :=
  xs.foldl (fun total pair => if i.val == pair.1 then total + pair.2 else total) 0

public def target (i : Fin 32) : Int := sparse [(11, 1), (25, 4)] i
public def degree7 (i : Fin 32) : Int := sparse [(0, 1), (2, 1), (5, 1), (11, 3), (15, 1), (19, 1), (23, 1), (24, 1)] i
public def r0 (i : Fin 32) : Int := sparse [(1, 2), (9, 1), (15, 1), (17, 1)] i
public def r4 (i : Fin 32) : Int := sparse [(1, 1), (9, 2), (13, 1), (19, 1)] i
public def r7 (i : Fin 32) : Int := sparse [(5, 1), (9, 1), (13, 2), (28, 1)] i
public def r10 (i : Fin 32) : Int := sparse [(1, 1), (17, 2), (18, 1), (23, 1)] i
public def r11 (i : Fin 32) : Int := sparse [(2, 1), (17, 1), (18, 2), (29, 1)] i
public def r13 (i : Fin 32) : Int := sparse [(1, 1), (9, 1), (13, 1), (17, 1), (18, 1), (25, 3), (28, 1), (29, 1)] i
public def r14 (i : Fin 32) : Int := sparse [(13, 1), (24, 1), (28, 2), (29, 1)] i
public def r15 (i : Fin 32) : Int := sparse [(0, 1), (18, 1), (28, 1), (29, 2)] i

/-- The corrected degree-2 row at source 25 is in the span of the
corrected degree-7 row at source 11 and eight archived rows. -/
public theorem exact_identity (i : Fin 32) :
  3 * target i = degree7 i - r0 i - r4 i - r7 i - r10 i - r11 i + 4 * r13 i - r14 i - r15 i := by
  fin_cases i <;> decide

#print axioms exact_identity

end MixedDegreeWitness
