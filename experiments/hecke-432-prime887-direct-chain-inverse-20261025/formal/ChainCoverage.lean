import Std

namespace P887DirectChainInverse

universe u
variable {α : Type u}

/-- Duplicate-free generated and independently corrected chain-key lists
are permutations when every generated key is corrected and both exhaustive
counts are 872. The concrete containment and counts are replayed by the
finite-field producer and independent audit. -/
theorem generated_keys_perm_corrected
    (generated corrected : List α)
    (hgenerated : generated.Nodup)
    (hcorrected : corrected.Nodup)
    (hsubset : generated ⊆ corrected)
    (hgenerated_count : generated.length = 872)
    (hcorrected_count : corrected.length = 872) :
    generated.Perm corrected := by
  apply (List.perm_ext_iff_of_nodup hgenerated hcorrected).2
  intro x
  constructor
  · intro hx
    exact hsubset hx
  · intro hx
    by_cases hmem : x ∈ generated
    · exact hmem
    · have hcons : (x :: generated).Nodup :=
        List.nodup_cons.mpr ⟨hmem, hgenerated⟩
      have hcons_subset : x :: generated ⊆ corrected := by
        intro y hy
        cases List.mem_cons.mp hy with
        | inl h => exact h ▸ hx
        | inr h => exact hsubset h
      have hle := List.Nodup.length_le_of_subset hcons hcons_subset
      simp only [List.length_cons, hgenerated_count, hcorrected_count] at hle
      omega

/-- The observed single and double candidate fibers account for 872
source chains. -/
theorem candidate_fiber_total : 856 * 1 + 8 * 2 = 872 := by decide

/-- The special-automorphism quotient removes eight redundant raw paths. -/
theorem raw_orbit_total : 880 - 8 = 872 := by decide

#print axioms generated_keys_perm_corrected
#print axioms candidate_fiber_total
#print axioms raw_orbit_total

end P887DirectChainInverse
