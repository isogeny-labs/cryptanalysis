import Std

namespace InverseTraceANF

/-- A full-column-rank evaluation map has no nonzero coefficient vector
whose evaluations all vanish. -/
theorem no_nonzero_annihilator_of_injective_eval
    {Coefficients Evaluations : Type}
    [Zero Coefficients] [Zero Evaluations]
    (evaluate : Coefficients → Evaluations)
    (hzero : evaluate 0 = 0)
    (hinjective : Function.Injective evaluate)
    (coefficients : Coefficients)
    (hvanishes : evaluate coefficients = 0) :
    coefficients = 0 := by
  apply hinjective
  exact hvanishes.trans hzero.symm

#print axioms no_nonzero_annihilator_of_injective_eval
end InverseTraceANF
