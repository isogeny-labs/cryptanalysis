import Std

namespace ExactCapacity

def reachable {A Q : Type} (codes : List A) (cover : A → List Q) : List Q :=
  codes.flatMap cover

/-- A fixed advice code selects at most `K` covered targets. -/
theorem reachable_length_le {A Q : Type} (codes : List A)
    (cover : A → List Q) (K : Nat)
    (h : ∀ a ∈ codes, (cover a).length ≤ K) :
    (reachable codes cover).length ≤ codes.length * K := by
  induction codes with
  | nil => simp [reachable]
  | cons a rest ih =>
      have ha : (cover a).length ≤ K := h a (by simp)
      have hr : ∀ b ∈ rest, (cover b).length ≤ K := by
        intro b hb
        exact h b (by simp [hb])
      have tail := ih hr
      simp only [reachable, List.flatMap_cons, List.length_append,
                 List.length_cons, Nat.succ_mul] at *
      omega

/-- Distinct successful targets fit in the union of the advice-specific
completion sets. Duplicate proposals only reduce that union. -/
theorem successful_targets_le {A Q : Type} [DecidableEq Q]
    (targets : List Q) (codes : List A) (cover : A → List Q)
    (advice : Q → A) (K : Nat) (hnodup : targets.Nodup)
    (hcodes : ∀ q ∈ targets, advice q ∈ codes)
    (hcover : ∀ a ∈ codes, (cover a).length ≤ K) :
    (targets.filter (fun q => decide (q ∈ cover (advice q)))).length ≤
      codes.length * K := by
  classical
  have hsubset : targets.filter (fun q => decide (q ∈ cover (advice q))) ⊆
      reachable codes cover := by
    intro q hq
    have hq' := List.mem_filter.mp hq
    exact List.mem_flatMap.mpr ⟨advice q, hcodes q hq'.1,
      of_decide_eq_true hq'.2⟩
  have hcount := List.Nodup.length_le_of_subset (hnodup.filter _) hsubset
  exact Nat.le_trans hcount (reachable_length_le codes cover K hcover)

def subgroupOrder : Nat := 680564733841876926932320129493409985129
def validCodes : Nat := 67109836
def signedStateCeiling : Nat := 4 * validCodes
def orderedPairCeiling : Nat := signedStateCeiling ^ 2

theorem exactStateUpper : signedStateCeiling = 268439344 := by decide
theorem exactPairUpper : orderedPairCeiling = 72059681407150336 := by decide

/-- One fixed outer proposal and at most 71 advice bits keep the rigorous
uniform-subgroup success upper bound below one half. -/
theorem oneProposalSeventyOneBitsInsufficient :
    2 * (2^71) * orderedPairCeiling < subgroupOrder := by decide
theorem oneProposalSeventyTwoBitsThreshold :
    subgroupOrder ≤ 2 * (2^72) * orderedPairCeiling := by decide

/-- Eight fixed outer proposals per advice value are an optimistic count
based on the measured complete terminal pass, not a throughput guarantee. -/
theorem eightProposalsSixtyEightBitsInsufficient :
    2 * (2^68) * 8 * orderedPairCeiling < subgroupOrder := by decide
theorem eightProposalsSixtyNineBitsThreshold :
    subgroupOrder ≤ 2 * (2^69) * 8 * orderedPairCeiling := by decide

theorem sixProposalsSixtyNineBitsInsufficient :
    2 * (2^69) * 6 * orderedPairCeiling < subgroupOrder := by decide
theorem sixProposalsSeventyBitsThreshold :
    subgroupOrder ≤ 2 * (2^70) * 6 * orderedPairCeiling := by decide

theorem twentyMillionFortySevenBitsInsufficient :
    2 * (2^47) * 20000000 * orderedPairCeiling < subgroupOrder := by decide
theorem twentyMillionFortyEightBitsThreshold :
    subgroupOrder ≤ 2 * (2^48) * 20000000 * orderedPairCeiling := by decide

#print axioms ExactCapacity.reachable_length_le
#print axioms ExactCapacity.successful_targets_le
#print axioms ExactCapacity.exactStateUpper
#print axioms ExactCapacity.exactPairUpper
#print axioms ExactCapacity.oneProposalSeventyOneBitsInsufficient
#print axioms ExactCapacity.oneProposalSeventyTwoBitsThreshold
#print axioms ExactCapacity.eightProposalsSixtyEightBitsInsufficient
#print axioms ExactCapacity.eightProposalsSixtyNineBitsThreshold
#print axioms ExactCapacity.sixProposalsSixtyNineBitsInsufficient
#print axioms ExactCapacity.sixProposalsSeventyBitsThreshold
#print axioms ExactCapacity.twentyMillionFortySevenBitsInsufficient
#print axioms ExactCapacity.twentyMillionFortyEightBitsThreshold

end ExactCapacity
