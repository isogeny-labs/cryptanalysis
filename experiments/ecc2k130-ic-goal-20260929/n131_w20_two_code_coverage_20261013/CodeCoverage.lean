import Std

/-! Finite counting for bounded lists of target-conditioned code proposals. -/
namespace CodeCoverage

variable {Code Target : Type}

def reachable (codes : List Code) (cover : Code → List Target) : List Target :=
  codes.flatMap cover

theorem reachable_length_le (codes : List Code) (cover : Code → List Target)
    (cap : Nat) (h : ∀ c ∈ codes, (cover c).length ≤ cap) :
    (reachable codes cover).length ≤ codes.length * cap := by
  induction codes with
  | nil => simp [reachable]
  | cons c rest ih =>
      have hc : (cover c).length ≤ cap := h c (by simp)
      have hr : ∀ d ∈ rest, (cover d).length ≤ cap := by
        intro d hd
        exact h d (by simp [hd])
      have tail := ih hr
      simp only [reachable, List.flatMap_cons, List.length_append,
                 List.length_cons, Nat.succ_mul] at *
      omega

theorem successful_targets_le [DecidableEq Target] (targets : List Target)
    (codes : List Code) (cover : Code → List Target)
    (advice : Target → Code) (cap : Nat)
    (hnodup : targets.Nodup)
    (hcodes : ∀ q ∈ targets, advice q ∈ codes)
    (hcover : ∀ c ∈ codes, (cover c).length ≤ cap) :
    (targets.filter (fun q => decide (q ∈ cover (advice q)))).length ≤
      codes.length * cap := by
  classical
  have hsubset : targets.filter (fun q => decide (q ∈ cover (advice q))) ⊆
      reachable codes cover := by
    intro q hq
    have hq' := List.mem_filter.mp hq
    exact List.mem_flatMap.mpr
      ⟨advice q, hcodes q hq'.1, of_decide_eq_true hq'.2⟩
  have hcount := List.Nodup.length_le_of_subset (hnodup.filter _) hsubset
  exact Nat.le_trans hcount (reachable_length_le codes cover cap hcover)

def r131 : Nat := 680564733841876926932320129493409985129
def s131 : Nat := 528180
def twoCodeCap : Nat := 16 * s131 ^ 5

theorem proposals_517380077_below_half :
    2 * (517380077 * twoCodeCap) < r131 := by decide

theorem proposals_517380078_reach_half_ceiling :
    r131 ≤ 2 * (517380078 * twoCodeCap) := by decide

#print axioms CodeCoverage.successful_targets_le
#print axioms CodeCoverage.proposals_517380077_below_half
#print axioms CodeCoverage.proposals_517380078_reach_half_ceiling
end CodeCoverage
