import Mathlib

namespace M31FourCoverage.Walk
/-- Balanced word counts of lengths 2, 4, 6 and 8. A new generator
appearing j times with each sign has choose(2k,2j)*choose(2j,j) placements. -/
def balanced : Nat → Nat × Nat × Nat × Nat
  | 0 => (0,0,0,0)
  | m+1 =>
    let (a,b,c,d) := balanced m
    (a+2, b+12*a+6, c+30*b+90*a+20, d+56*c+420*b+560*a+70)

set_option maxRecDepth 8000 in
theorem balanced_195 : balanced 195 = (390,455130,882956100,2391959893050) := by
  decide +kernel

/-- With other generators fixed, a nonzero coefficient in the prime-order
cyclic model admits exactly one value of its generator for any chosen sum. -/
theorem unique_completion {F : Type*} [Field F] (c r y : F) (h : c ≠ 0) :
    ∃! x, c*x+r=y := by
  refine ⟨(y-r)/c, ?_, ?_⟩
  · field_simp
    ring
  · intro x hx
    apply (eq_div_iff h).mpr
    linear_combination hx

end M31FourCoverage.Walk
