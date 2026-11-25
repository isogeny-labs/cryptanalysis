import Mathlib.Tactic

namespace NativeSmooth

def strip (q x : ℕ) : ℕ :=
  if _h : 1 < q ∧ 0 < x ∧ x % q = 0 then strip q (x/q) else x
termination_by x
decreasing_by exact Nat.div_lt_self _h.2.1 _h.1

theorem strip_eq (q x : ℕ) (hp : q.Prime) : strip q x = ordCompl[q] x := by
  induction x using Nat.strong_induction_on with
  | h x ih =>
    rw [strip]
    split
    · rename_i h
      rw [ih _ (Nat.div_lt_self h.2.1 h.1), Nat.ordCompl_div_of_dvd hp (Nat.dvd_of_mod_eq_zero h.2.2)]
    · rename_i h
      apply Eq.symm
      apply (Nat.ordCompl_eq_self_iff_zero_or_not_dvd x hp).2
      by_cases hz : x = 0
      · exact Or.inl hz
      · exact Or.inr (fun hd => h ⟨hp.one_lt, Nat.pos_of_ne_zero hz, Nat.mod_eq_zero_of_dvd hd⟩)

def residual : List ℕ → ℕ → ℕ
  | [], x => x
  | q::qs, x => residual qs (strip q x)

def early : List ℕ → ℕ → Bool
  | [], _ => false
  | q::qs, x => decide (strip q x ≤ 211) || early qs (strip q x)

theorem residual_dvd (qs : List ℕ) (x : ℕ) (hp : ∀ q ∈ qs, Nat.Prime q) :
    residual qs x ∣ x := by
  induction qs generalizing x with
  | nil => exact dvd_refl _
  | cons q qs ih =>
    rw [residual, strip_eq q x (hp q (by simp))]
    exact (ih _ (fun r hr => hp r (by simp [hr]))).trans (Nat.ordCompl_dvd x q)

theorem residual_pos (qs : List ℕ) (x : ℕ) (hx : 0 < x) (hp : ∀ q ∈ qs, Nat.Prime q) :
    0 < residual qs x := Nat.pos_of_dvd_of_pos (residual_dvd qs x hp) hx

theorem early_iff (qs : List ℕ) (x : ℕ) (hx : 0 < x) (hne : qs ≠ [])
    (hp : ∀ q ∈ qs, Nat.Prime q) : early qs x = true ↔ residual qs x ≤ 211 := by
  induction qs generalizing x with
  | nil => contradiction
  | cons q qs ih =>
    have hq := hp q (by simp)
    have ht : ∀ r ∈ qs, Nat.Prime r := fun r hr => hp r (by simp [hr])
    have hs : 0 < strip q x := by rw [strip_eq q x hq]; exact Nat.ordCompl_pos q hx.ne'
    by_cases he : qs = []
    · subst qs; simp [early,residual]
    · simp only [early, Bool.or_eq_true, decide_eq_true_eq, residual, ih _ hs he ht]
      exact or_iff_right_of_imp (fun h => (Nat.le_of_dvd hs (residual_dvd _ _ ht)).trans h)

theorem residual_factor (qs : List ℕ) (x r : ℕ) (hp : ∀ q ∈ qs, Nat.Prime q) :
    (residual qs x).factorization r = if r ∈ qs then 0 else x.factorization r := by
  induction qs generalizing x with
  | nil => simp [residual]
  | cons q qs ih =>
    rw [residual, ih _ (fun s hs => hp s (by simp [hs])), strip_eq q x (hp q (by simp)),
        Nat.factorization_ordCompl]
    by_cases hr : r ∈ qs <;> by_cases he : r = q <;>
      simp [hr, he]

def factors : List ℕ :=
  [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,
   101,103,107,109,113,127,131,137,139,149,151,157,163,167,173,179,181,191,
   193,197,199,211]

theorem mem_factors (q : ℕ) : q ∈ factors ↔ q ≤ 211 ∧ q.Prime := by
  have he : factors = (List.range 212).filter (fun n => decide n.Prime) := by decide +kernel
  simp [he, Nat.lt_succ_iff]

theorem native_filter (x : ℕ) (hx : 0 < x) :
    early factors x = true ↔ ∀ q : ℕ, q.Prime → q ∣ x → q ≤ 211 := by
  have hp : ∀ q ∈ factors, Nat.Prime q := fun q h => ((mem_factors q).1 h).2
  have hr := residual_pos factors x hx hp
  rw [early_iff _ _ hx (by decide) hp]
  constructor
  · intro h q hq hd
    by_contra! hbig
    have hnot : q ∉ factors := by simp [mem_factors, hbig.not_ge]
    have hf := hq.factorization_pos_of_dvd hx.ne' hd
    rw [← ite_eq_right hnot (α := ℕ) (t := 0) (e := x.factorization q)] at hf
    rw [← residual_factor factors x q hp] at hf
    exact hbig.not_ge ((Nat.le_of_dvd hr (Nat.dvd_of_factorization_pos hf.ne')).trans h)
  · intro h
    by_contra! hbig
    let y := residual factors x
    have hy : y ≠ 1 := by dsimp [y]; omega
    have hq := Nat.minFac_prime hy
    have hd := Nat.minFac_dvd y
    have hm := (mem_factors _).2 ⟨h _ hq (hd.trans (residual_dvd factors x hp)),hq⟩
    have hf := hq.factorization_pos_of_dvd hr.ne' hd
    change 0 < (residual factors x).factorization y.minFac at hf
    rw [residual_factor _ _ _ hp, ite_eq_left hm] at hf
    omega

def accepts (x : ℕ) : Bool := decide (x ≠ 0) && early factors x

theorem signed_filter (x p : ℕ) :
    accepts (min x (p-x)) = true ↔
      min x (p-x) ≠ 0 ∧ ∀ q : ℕ, q.Prime → q ∣ min x (p-x) → q ≤ 211 := by
  by_cases hz : min x (p-x) = 0
  · simp [accepts, hz]
  · simp [accepts, hz, native_filter _ (Nat.pos_of_ne_zero hz)]

end NativeSmooth
