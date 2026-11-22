import Std

namespace P1231ChainCoverage

universe u
variable {α : Type u}

/-- The independently audited containment and equal count imply that the
generated source-key list is a permutation of the all-j source census. -/
theorem generated_keys_perm_sources
    (generated sources : List α)
    (hgenerated : generated.Nodup)
    (hsources : sources.Nodup)
    (hsubset : generated ⊆ sources)
    (hgenerated_count : generated.length = 1440)
    (hsource_count : sources.length = 1440) :
    generated.Perm sources := by
  apply (List.perm_ext_iff_of_nodup hgenerated hsources).2
  intro x
  constructor
  · intro hx
    exact hsubset hx
  · intro hx
    by_cases hmem : x ∈ generated
    · exact hmem
    · have hcons : (x :: generated).Nodup :=
        List.nodup_cons.mpr ⟨hmem, hgenerated⟩
      have hcons_subset : x :: generated ⊆ sources := by
        intro y hy
        cases List.mem_cons.mp hy with
        | inl h => exact h ▸ hx
        | inr h => exact hsubset h
      have hle := List.Nodup.length_le_of_subset hcons hcons_subset
      simp only [List.length_cons, hgenerated_count, hsource_count] at hle
      omega

theorem fiber_total : 1296 + 72 = 1368 ∧ 1296 + 2 * 72 = 1440 := by decide

#print axioms generated_keys_perm_sources
#print axioms fiber_total

end P1231ChainCoverage
