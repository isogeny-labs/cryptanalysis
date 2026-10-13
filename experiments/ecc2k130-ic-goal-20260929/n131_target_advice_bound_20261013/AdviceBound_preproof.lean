import Std

/-! A bounded target-advice alphabet selects one precomputed completion list.
Any successful target is in the union of those lists, whose length is bounded
by the alphabet size times the per-advice list bound. -/
namespace AdviceBound

variable {A Q : Type}

def reachable (codes : List A) (cover : A → List Q) : List Q :=
  codes.flatMap cover

theorem reachable_length_le (codes : List A) (cover : A → List Q) (K : Nat)
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

theorem selected_mem_reachable (codes : List A) (cover : A → List Q)
    (advice : Q → A) (q : Q) (hc : advice q ∈ codes)
    (hm : q ∈ cover (advice q)) :
    q ∈ reachable codes cover := by
  exact List.mem_flatMap.mpr ⟨advice q, hc, hm⟩

#print axioms AdviceBound.reachable_length_le
#print axioms AdviceBound.selected_mem_reachable
end AdviceBound
