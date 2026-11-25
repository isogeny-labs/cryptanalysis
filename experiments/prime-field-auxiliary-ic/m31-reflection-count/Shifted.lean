import MixedBuckets

namespace M31Reflection.Shifted
open Finset
variable {K : Type*} [Field K]

def A (c : K) := 3*c^2-4
def B (c : K) := -3*c^4+84*c-4
def D (c : K) := (cubic c)^2
def G (c u : K) := -u^3+A c*u^2+B c*u+D c
def L (c x : K) := x^3+A c*x^2-B c*x+D c
def R (c x : K) := x^3+B c*x^2+A c*D c*x-(D c)^2

def EL (c : K) : WeierstrassCurve.Affine K := ⟨0,A c,0,-B c,D c⟩
def ER (c : K) : WeierstrassCurve.Affine K := ⟨0,B c,0,A c*D c,-(D c)^2⟩

private theorem disc (c : K) :
    (EL c).Δ = -85184*(cubic (-2*c))^2 ∧
    (ER c).Δ = (D c)^2*(EL c).Δ := by
  constructor <;> simp only [EL, ER, WeierstrassCurve.Δ, WeierstrassCurve.b₂,
    WeierstrassCurve.b₄, WeierstrassCurve.b₆, WeierstrassCurve.b₈, A, B, D, cubic] <;> ring

theorem smooth_all (c : F) : (EL c).Δ ≠ 0 ∧ (ER c).Δ ≠ 0 := by
  have nz (t : F) : cubic t ≠ 0 := M31FixtureObstruction.no_root t
  have hl := (disc c).1.trans_ne (mul_ne_zero (by native_decide) (pow_ne_zero _ (nz _)))
  exact ⟨hl, (disc c).2.trans_ne (mul_ne_zero (pow_ne_zero _ (pow_ne_zero _ (nz c))) hl)⟩

section Sum
variable [Fintype K] [DecidableEq K]
local notation "χ" => quadraticChar K

private theorem split_sum (odd : ringChar K ≠ 2) (c : K) (hd : D c ≠ 0) :
    ∑ z, χ (cubic (c+z)*cubic (c-z)) =
    (∑ x, χ (L c x)) + (∑ x, χ (R c x)) - χ (R c 0) := by
  classical
  have prodEq (z : K) : cubic (c+z)*cubic (c-z) = G c (z^2) := by
    unfold G A B D cubic; ring
  have leq (u : K) : G c u = L c (-u) := by unfold G L; ring
  have req (u : K) : χ (u*G c u) =
      χ (R c (D c*u⁻¹)) - (if u = 0 then χ (R c 0) else 0) := by
    by_cases hz : u = 0
    · simp [hz]
    · simp only [hz, ↓reduceIte, sub_zero]
      have e : R c (D c*u⁻¹) = (D c*u⁻¹^2)^2*(u*G c u) := by
        unfold R G; field_simp; ring
      rw [e, map_mul (quadraticChar K) (_^2), quadraticChar_sq_one'
        (mul_ne_zero hd (pow_ne_zero _ (inv_ne_zero hz))), one_mul]
  have a := Equiv.sum_comp (Equiv.neg K) (fun v => χ (L c v))
  have b := Equiv.sum_comp ((Equiv.inv K).trans (Equiv.mulLeft₀ (D c) hd)) (fun v => χ (R c v))
  change (∑ u : K, χ (L c (-u))) = _ at a
  change (∑ u : K, χ (R c (D c*u⁻¹))) = _ at b
  simp_rw [prodEq]
  rw [square_sum odd (fun u => χ (G c u))]
  simp only [add_mul, one_mul, ← map_mul, sum_add_distrib, req, sum_sub_distrib]
  simp_rw [leq]
  rw [a,b]
  simp
  ring

end Sum

private theorem left_eqn (c x y : K) (hd : (EL c).Δ ≠ 0) :
    (EL c).Nonsingular x y ↔ y^2 = L c x := by
  rw [← (EL c).equation_iff_nonsingular_of_Δ_ne_zero hd, (EL c).equation_iff]
  simp [EL,L]; ring_nf

private theorem right_eqn (c x y : K) (hd : (ER c).Δ ≠ 0) :
    (ER c).Nonsingular x y ↔ y^2 = R c x := by
  rw [← (ER c).equation_iff_nonsingular_of_Δ_ne_zero hd, (ER c).equation_iff]
  simp [ER,R]; ring_nf

private theorem zeroEq (v : K) : R v 0 = (-1)*(D v)^2 := by unfold R; ring

theorem correlation (c : F) :
    ∑ z, quadraticChar F (cubic (c+z)*cubic (c-z)) =
    (Nat.card (EL c).Point : ℤ) + Nat.card (ER c).Point - 4294967295 := by
  have odd : ringChar F ≠ 2 := (ZMod.ringChar_zmod_n _).trans_ne (by decide)
  have hd : D c ≠ 0 := pow_ne_zero _ (M31FixtureObstruction.no_root c)
  have a := trace_sum odd (EL c) (L c) (fun x y => left_eqn c x y (smooth_all c).1)
  have b := trace_sum odd (ER c) (R c) (fun x y => right_eqn c x y (smooth_all c).2)
  rw [ZMod.card] at a b
  have sign : quadraticChar F (-1) = -1 := by
    apply quadraticChar_neg_one_iff_not_isSquare.mpr
    intro hs
    exact (by decide : ¬(2147483647 % 4 ≠ 3)) (ZMod.exists_sq_eq_neg_one_iff.mp hs)
  have correction : quadraticChar F (R c 0) = -1 := by
    rw [zeroEq c, map_mul, quadraticChar_sq_one' hd, mul_one]
    exact sign
  apply (split_sum odd c hd).trans
  rw [correction]
  have close (l r s t : ℤ) (a : l = s + (2147483647+1)) (b : r = t + (2147483647+1)) :
      s+t-(-1) = l+r-4294967295 := by omega
  exact close _ _ _ _ a b

private def label (c z : F) := IsSquare (cubic (c+z))

/-- Offset z is the smaller of z and −z, and the lift labels differ. -/
def mixed (c z : F) := z.val < (-z).val ∧ ¬ (label c z ↔ label c (-z))

private noncomputable def mark (c z : F) : ℤ := by
  classical exact if mixed c z then 1 else 0

noncomputable def buckets (c : F) : Finset F := by
  classical exact univ.filter (mixed c)

private theorem point_contribution (c z : F) : quadraticChar F (cubic (c+z)*cubic (c-z)) =
    1-2*(mark c z + mark c (-z)) := by
  classical
  rw [map_mul, sign_at, sign_at]
  rw [sub_eq_add_neg c z]
  unfold mark mixed label
  have nz : - -z = z := neg_neg z
  erw [nz]
  rcases lt_trichotomy z.val (-z).val with h | h | h
  · have hr := not_lt_of_gt h
    by_cases a : IsSquare (cubic (c+z)) <;> by_cases b : IsSquare (cubic (c+(-z))) <;> simp [a,b,h,hr] <;> exact b
  · have fixed := ZMod.val_injective 2147483647 h
    erw [← fixed]
    by_cases a : IsSquare (cubic (c+z)) <;> simp [a]
  · have hr := not_lt_of_gt h
    by_cases a : IsSquare (cubic (c+z)) <;> by_cases b : IsSquare (cubic (c+(-z))) <;> simp [a,b,h,hr] <;> exact b

theorem bucket_identity (c : F) : 4*((buckets c).card : ℤ) =
    6442450942 - Nat.card (EL c).Point - Nat.card (ER c).Point := by
  classical
  have h := correlation c
  simp_rw [point_contribution] at h
  rw [sum_sub_distrib, ← mul_sum, sum_add_distrib] at h
  have perm : (∑ z : F, mark c (-z)) = ∑ z : F, mark c z := Equiv.sum_comp (Equiv.neg F) (mark c)
  have total : (∑ _ : F, (1 : ℤ)) = 2147483647 := by simp [F, ZMod.card]
  have cnt : (∑ z : F, mark c z) = ((buckets c).card : ℤ) := Finset.sum_boole (mixed c) univ
  rw [total, perm, cnt] at h
  omega

/-- The two squared Hasse bounds imply a uniform interval for all centers. -/
theorem range_of_hasse (c : F)
    (hl : ((Nat.card (EL c).Point : ℤ)-2147483648)^2 ≤ 4*2147483647)
    (hr : ((Nat.card (ER c).Point : ℤ)-2147483648)^2 ≤ 4*2147483647) :
    536824571 ≤ (buckets c).card ∧ (buckets c).card ≤ 536917252 := by
  have interval (x : ℤ) (h : (x-2147483648)^2 ≤ 4*2147483647) :
      2147390967 ≤ x ∧ x ≤ 2147576329 := by
    constructor
    · by_contra! e
      have v : x ≤ 2147390966 := by omega
      nlinarith [mul_nonneg (show 0 ≤ 2147390966-x by omega) (show 0 ≤ 2147390966-x by omega)]
    · by_contra! e
      have v : 2147576330 ≤ x := by omega
      nlinarith [mul_nonneg (show 0 ≤ x-2147576330 by omega) (show 0 ≤ x-2147576330 by omega)]
  have l := interval _ hl
  have r := interval _ hr
  have b := bucket_identity c
  omega


/-- Prediction errors indexed by displacement from the center. -/
noncomputable def errors (c : F) (guess : F → Prop) : Finset F := by
  classical exact univ.filter (fun z => ¬ (guess z ↔ label c z))

/-- Inject mixed representatives into distinct erroneous predictions. -/
theorem mixed_le_errors (c : F) (guess : F → Prop) (shared : ∀ z, guess z ↔ guess (-z)) :
    (buckets c).card ≤ (errors c guess).card := by
  classical
  let pick (z : F) := if (guess z ↔ label c z) then -z else z
  have member {z : F} (hz : z ∈ buckets c) : mixed c z := (mem_filter.mp hz).2
  apply card_le_card_of_injOn pick
  · intro z hz
    apply mem_filter.mpr
    refine ⟨mem_univ _, ?_⟩
    dsimp only [pick]
    split_ifs with ok
    · intro ok'
      exact (member hz).2 ((ok.symm.trans (shared z)).trans ok')
    · exact ok
  · let key (z : F) := min z.val (-z).val
    have recover {z : F} (hz : z ∈ buckets c) : key (pick z) = z.val := by
      have h := (member hz).1.le
      dsimp only [key, pick]
      split_ifs
      · have back := congrArg (fun t : F => t.val) (neg_neg z)
        exact (congrArg (min (-z).val) back).trans (min_eq_right h)
      · exact min_eq_left h
    intro z hz t ht eq
    exact ZMod.val_injective 2147483647 ((recover hz).symm.trans ((congrArg key eq).trans (recover ht)))

theorem prediction_lower_bound (c : F) (guess : F → Prop) (shared : ∀ z, guess z ↔ guess (-z))
    (hl : ((Nat.card (EL c).Point : ℤ)-2147483648)^2 ≤ 4*2147483647)
    (hr : ((Nat.card (ER c).Point : ℤ)-2147483648)^2 ≤ 4*2147483647) :
    536824571 ≤ (errors c guess).card :=
  (range_of_hasse c hl hr).1.trans (mixed_le_errors c guess shared)


/-- Using the label of the smaller offset attains exactly the mixed-bucket count. -/
theorem attainable (c : F) : ∃ guess : F → Prop,
    (∀ z, guess z ↔ guess (-z)) ∧ (errors c guess).card = (buckets c).card := by
  classical
  let rep (z : F) := if z.val ≤ (-z).val then z else -z
  have valrep (z : F) : (rep z).val = min z.val (-z).val := by
    dsimp [rep]
    split_ifs with h
    · exact (min_eq_left h).symm
    · exact (min_eq_right (by omega)).symm
  let guess (z : F) := label c (rep z)
  have shared (z : F) : guess z ↔ guess (-z) := by
    have back := congrArg (fun t : F => t.val) (neg_neg z)
    have swap := (congrArg (min (-z).val) back).trans (min_comm _ _)
    have eq := (valrep (-z)).trans (swap.trans (valrep z).symm)
    exact (congrArg (label c) (ZMod.val_injective 2147483647 eq).symm).to_iff
  refine ⟨guess, shared, le_antisymm ?_ (mixed_le_errors c guess shared)⟩
  apply card_le_card_of_injOn (fun z : F => -z)
  · intro z hz
    have bad : ¬ (label c (rep z) ↔ label c z) := (mem_filter.mp hz).2
    by_cases h : z.val ≤ (-z).val
    · have fixed : rep z = z := by simp [rep, h]
      exact (bad ((congrArg (label c) fixed).to_iff)).elim
    · have other : rep z = -z := by simp [rep, h]
      have opposite : ¬ (label c (-z) ↔ label c z) := fun same =>
        bad (((congrArg (label c) other).to_iff).trans same)
      apply mem_filter.mpr
      refine ⟨mem_univ _, ?_⟩
      unfold mixed
      erw [neg_neg z]
      exact ⟨lt_of_not_ge h, opposite⟩
  · intro _ _ _ _ eq
    exact neg_injective eq

/-- Every nonidentity affine involution in odd characteristic reflects about b/2. -/
theorem affine_center (a b : K) (two : (2 : K) ≠ 0)
    (inv : ∀ x, a*(a*x+b)+b = x) (nontrivial : ¬ (a = 1 ∧ b = 0)) :
    ∀ z, a*(b/2+z)+b = b/2-z := by
  have zero := inv 0
  have one := inv 1
  have square : (a-1)*(a+1) = 0 := by linear_combination one - zero
  have minus : a = -1 := by
    rcases mul_eq_zero.mp square with h | h
    · have ha : a = 1 := sub_eq_zero.mp h
      subst a
      simp only [one_mul, zero_add] at zero
      exact (nontrivial ⟨rfl, (mul_eq_zero.mp (show 2*b = 0 by linear_combination zero)).resolve_left two⟩).elim
    · exact eq_neg_of_add_eq_zero_left h
  intro z
  rw [minus]
  field_simp
  ring

end M31Reflection.Shifted
