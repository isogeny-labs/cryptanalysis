import Std

/-! A source-dependent fixed suffix exposes only its two-code completion
list. Advice selects one list of suffix proposals for each target. -/
namespace FixedSuffixCoverage

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

theorem successful_targets_le [DecidableEq Q] (targets : List Q) (codes : List A)
    (cover : A → List Q) (advice : Q → A) (K : Nat)
    (hnodup : targets.Nodup)
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

theorem bounded_advice_suffix_success {S : Type} [DecidableEq Q]
    (targets : List Q) (codes : List A) (suffixes : A → List S)
    (finish : S → List Q) (advice : Q → A) (k M : Nat)
    (hnodup : targets.Nodup)
    (hcodes : ∀ q ∈ targets, advice q ∈ codes)
    (hsuffixes : ∀ a ∈ codes, (suffixes a).length ≤ k)
    (hfinish : ∀ a ∈ codes, ∀ s ∈ suffixes a, (finish s).length ≤ M) :
    (targets.filter (fun q =>
      decide (q ∈ (suffixes (advice q)).flatMap finish))).length ≤
      codes.length * (k * M) := by
  let cover : A → List Q := fun a => (suffixes a).flatMap finish
  have hcover : ∀ a ∈ codes, (cover a).length ≤ k * M := by
    intro a ha
    have h := reachable_length_le (suffixes a) finish M (hfinish a ha)
    exact Nat.le_trans h (Nat.mul_le_mul_right M (hsuffixes a ha))
  exact successful_targets_le targets codes cover advice (k * M)
    hnodup hcodes hcover

theorem n131_pair_bound :
    16 * ((268435456 * (268435456 - 1)) / 2) =
      576460750155939840 := by decide

theorem n131_billion_scaled_bound :
    600000000000 * 576460750155939840 * 1000000000 <
      680564733841876926932320129493409985129 := by decide

#print axioms reachable_length_le
#print axioms successful_targets_le
#print axioms bounded_advice_suffix_success
#print axioms n131_pair_bound
#print axioms n131_billion_scaled_bound

end FixedSuffixCoverage
