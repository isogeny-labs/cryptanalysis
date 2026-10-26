import Std

namespace CrossprimeDirectChainInverse

universe u
variable {α : Type u}

/-- A duplicate-free list of generated source-chain keys is an exhaustive
permutation of the independent frozen source list once containment and the
two cardinalities have been checked. The finite-field audit supplies these
hypotheses for the p883 and p997 data. -/
theorem generated_keys_perm_sources
    (generated sources : List α)
    (hgenerated : generated.Nodup)
    (hsources : sources.Nodup)
    (hsubset : generated ⊆ sources)
    (hgenerated_count : generated.length = 2664)
    (hsource_count : sources.length = 2664) :
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

theorem source_count : 864 + 1800 = 2664 := by decide

#print axioms generated_keys_perm_sources
#print axioms source_count

end CrossprimeDirectChainInverse
