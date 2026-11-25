import Std

namespace P919DirectInverse

universe u
variable {α : Type u}

/-- Complete generated chain-key containment and equal source-key count
imply permutation when both enumerations are duplicate-free. The concrete
containment and counts are checked by the independent finite-field audit. -/
theorem generated_keys_perm_sources
    (generated sources : List α)
    (hgenerated : generated.Nodup)
    (hsources : sources.Nodup)
    (hsubset : generated ⊆ sources)
    (hgenerated_count : generated.length = 1296)
    (hsource_count : sources.length = 1296) :
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

theorem fiber_count : 1152 + 72 = 1224 ∧ 1152 + 2 * 72 = 1296 := by decide

#print axioms generated_keys_perm_sources
#print axioms fiber_count

end P919DirectInverse
