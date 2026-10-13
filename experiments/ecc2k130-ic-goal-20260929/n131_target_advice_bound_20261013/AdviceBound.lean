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

theorem successful_targets_le [DecidableEq Q] (targets : List Q) (codes : List A)
    (cover : A → List Q) (advice : Q → A) (K : Nat)
    (hnodup : targets.Nodup)
    (hcodes : ∀ q ∈ targets, advice q ∈ codes)
    (hcover : ∀ a ∈ codes, (cover a).length ≤ K) :
    (targets.filter (fun q => decide (q ∈ cover (advice q)))).length ≤ codes.length * K := by
  classical
  have hsubset : targets.filter (fun q => decide (q ∈ cover (advice q))) ⊆
      reachable codes cover := by
    intro q hq
    have hq' := List.mem_filter.mp hq
    exact selected_mem_reachable codes cover advice q (hcodes q hq'.1)
      (of_decide_eq_true hq'.2)
  have hcount := List.Nodup.length_le_of_subset (hnodup.filter _) hsubset
  exact Nat.le_trans hcount (reachable_length_le codes cover K hcover)

#print axioms AdviceBound.reachable_length_le
#print axioms AdviceBound.selected_mem_reachable
#print axioms AdviceBound.successful_targets_le
end AdviceBound
