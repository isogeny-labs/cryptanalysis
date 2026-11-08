/-!
The GLV cap confirmation's no-worse rule inspects only pooled-size lower
endpoints. The archived j=0 family interval is a separate descriptive output.
These theorems concern the exact decimal endpoints printed in results.json,
scaled by 10^16. They make no statistical-coverage or execution claim.
-/

namespace GLVCapNoWorse

structure Interval where
  lower : Nat
  upper : Nat

def one : Nat := 10000000000000000

def wellFormed (i : Interval) : Prop := i.lower ≤ i.upper

def noWorsePass (pooledSizes : List Interval) : Prop :=
  pooledSizes.all (fun i => decide (i.lower ≤ one)) = true

def allWellFormed (intervals : List Interval) : Prop :=
  intervals.all (fun i => decide (i.lower ≤ i.upper)) = true

def pooled40to43 : List Interval :=
  [⟨9633305383496846, 10206439763276927⟩,
   ⟨9607939208626060, 10185748136395380⟩,
   ⟨9539100281038944, 10106357048268606⟩,
   ⟨9495902517552110, 10071181450938511⟩]

def j0Family : Interval :=
  ⟨9860137324692078, 10186699532206690⟩

def j0PointEstimate : Nat := 10019840110118106

theorem published_pooled_noWorsePass : noWorsePass pooled40to43 := by
  unfold noWorsePass pooled40to43 one
  decide

theorem published_pooled_wellFormed : allWellFormed pooled40to43 := by
  unfold allWellFormed pooled40to43
  decide

theorem published_j0_straddles_one :
    j0Family.lower < one ∧ one < j0Family.upper := by
  decide

theorem published_j0_point_above_one : one < j0PointEstimate := by
  decide

theorem published_j0_wellFormed : wellFormed j0Family := by
  unfold wellFormed j0Family
  decide

theorem published_j0_not_bounded_by_pooled_pass :
    noWorsePass pooled40to43 ∧ ¬ j0Family.upper ≤ one := by
  exact ⟨published_pooled_noWorsePass, by decide⟩

theorem pooled_pass_does_not_bound_family_upper :
    ¬ (∀ (pooledSizes : List Interval) (family : Interval),
      allWellFormed pooledSizes → wellFormed family →
      noWorsePass pooledSizes → family.upper ≤ one) := by
  intro h
  have upperBound := h pooled40to43 j0Family
    published_pooled_wellFormed published_j0_wellFormed
    published_pooled_noWorsePass
  have upperNotBound : ¬ j0Family.upper ≤ one := by decide
  exact upperNotBound upperBound

#print axioms published_pooled_noWorsePass
#print axioms published_pooled_wellFormed
#print axioms published_j0_straddles_one
#print axioms published_j0_point_above_one
#print axioms published_j0_wellFormed
#print axioms published_j0_not_bounded_by_pooled_pass
#print axioms pooled_pass_does_not_bound_family_upper

end GLVCapNoWorse
