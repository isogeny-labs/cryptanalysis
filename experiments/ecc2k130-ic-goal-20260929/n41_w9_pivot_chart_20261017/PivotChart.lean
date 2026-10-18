import Std

namespace PivotChart

/-- A chart decoder that is a left inverse on the full linear image recovers
the unique code satisfying the full equation. The syndrome check is exact. -/
theorem decoded_iff_full_equation {Code Output Chart : Type}
    (encode : Code → Output) (project : Output → Chart)
    (decode : Chart → Code)
    (leftInverse : ∀ code, decode (project (encode code)) = code)
    (target : Output) (code : Code) :
    (decode (project target) = code ∧ encode code = target) ↔
    encode code = target := by
  constructor
  · exact And.right
  · intro equal
    constructor
    · rw [← equal]
      exact leftInverse code
    · exact equal

/-- A left inverse of the projected encoding proves injectivity of that
projection, so no second code can pass the full equation. -/
theorem projected_injective {Code Output Chart : Type}
    (encode : Code → Output) (project : Output → Chart)
    (decode : Chart → Code)
    (leftInverse : ∀ code, decode (project (encode code)) = code) :
    Function.Injective (project ∘ encode) := by
  intro code₁ code₂ equal
  have := congrArg decode equal
  simpa [Function.comp_def, leftInverse] using this

#print axioms PivotChart.decoded_iff_full_equation
#print axioms PivotChart.projected_injective

end PivotChart
