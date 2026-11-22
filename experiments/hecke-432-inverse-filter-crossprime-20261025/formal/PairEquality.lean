import Std

namespace CrossPrimeInverseFilter

universe u
variable {α : Type u}

/-- A complete source-pair list and a complete valid-root list contain the
same elements when the lists are duplicate-free, source pairs are valid,
and the independently counted lengths agree. -/
theorem source_pairs_perm_valid
    (source valid : List α)
    (hsource : source.Nodup)
    (hvalid : valid.Nodup)
    (hsub : source ⊆ valid)
    (hlen : source.length = valid.length) :
    source.Perm valid := by
  apply (List.perm_ext_iff_of_nodup hsource hvalid).2
  intro x
  constructor
  · intro hx
    exact hsub hx
  · intro hx
    by_cases hmem : x ∈ source
    · exact hmem
    ·
      have hcons : (x :: source).Nodup := List.nodup_cons.mpr ⟨hmem, hsource⟩
      have hcons_sub : x :: source ⊆ valid := by
        intro y hy
        cases List.mem_cons.mp hy with
        | inl h => exact h ▸ hx
        | inr h => exact hsub h
      have hle := List.Nodup.length_le_of_subset hcons hcons_sub
      simp only [List.length_cons, ← hlen] at hle
      omega

/-- The exceptional p887 count is arithmetically compatible with the full
rational resolvent count; the concrete partitions are audited separately. -/
theorem p887_count_partition : 864 + 8 = 872 := by decide

#print axioms source_pairs_perm_valid
#print axioms p887_count_partition

end CrossPrimeInverseFilter
