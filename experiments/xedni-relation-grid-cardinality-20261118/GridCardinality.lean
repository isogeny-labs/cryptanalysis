import Mathlib.Data.Fintype.Fin
import Mathlib.Data.Fintype.Prod
import Mathlib.Data.Fin.Rev
import Mathlib.Data.Finset.Prod
import Mathlib.Data.Finset.Card
import Mathlib.Data.Int.GCD
import Mathlib.Data.ZMod.Basic
import Lean.Elab.Tactic.Omega
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

/-! Exact cardinality of primitive linear images of a finite coefficient grid. -/

namespace XedniGridCardinality

def grid (L : ℕ) : Finset (Fin L × Fin L) := Finset.univ

def start (a b : ℕ) {L : ℕ} (p : Fin L × Fin L) : Prop :=
  p.1.val < a ∨ p.2.val < b

noncomputable def starts (L a b : ℕ) : Finset (Fin L × Fin L) := by
  classical exact (grid L).filter (start a b)

theorem card_starts (L a b : ℕ) :
    (starts L a b).card = L ^ 2 - (L - a) * (L - b) := by
  classical
  have hcomp : (starts L a b).card +
      ((Finset.univ.filter (fun i : Fin L => a ≤ i.val)).product
       (Finset.univ.filter (fun i : Fin L => b ≤ i.val))).card = L ^ 2 := by
    have hdisj : Disjoint (starts L a b)
        ((Finset.univ.filter (fun i : Fin L => a ≤ i.val)).product
         (Finset.univ.filter (fun i : Fin L => b ≤ i.val))) := by
      apply Finset.disjoint_left.mpr
      intro p hp hq
      have hp' : p.1.val < a ∨ p.2.val < b := by simpa [starts, grid, start] using hp
      have hq' : a ≤ p.1.val ∧ b ≤ p.2.val := by
        simpa [Finset.mem_product] using hq
      omega
    have hunion : (starts L a b) ∪
        ((Finset.univ.filter (fun i : Fin L => a ≤ i.val)).product
         (Finset.univ.filter (fun i : Fin L => b ≤ i.val))) = grid L := by
      ext ⟨u,v⟩
      by_cases hu : u.val < a <;> by_cases hv : v.val < b <;>
        simp [starts, grid, start, hu, hv, Finset.mem_product] <;> omega
    have h := Finset.card_union_of_disjoint hdisj
    rw [hunion] at h
    simpa [grid, pow_two] using h.symm
  have hnonA : (Finset.univ.filter (fun i : Fin L => a ≤ i.val)).card = L - a := by
    have hh := Finset.card_filter_add_card_filter_not (s := (Finset.univ : Finset (Fin L))) (p := fun i => i.val < a)
    simp only [Finset.card_univ, Fintype.card_fin] at hh
    simp only [not_lt] at hh
    rw [Fin.card_filter_val_lt] at hh
    omega
  have hnonB : (Finset.univ.filter (fun i : Fin L => b ≤ i.val)).card = L - b := by
    have hh := Finset.card_filter_add_card_filter_not (s := (Finset.univ : Finset (Fin L))) (p := fun i => i.val < b)
    simp only [Finset.card_univ, Fintype.card_fin] at hh
    simp only [not_lt] at hh
    rw [Fin.card_filter_val_lt] at hh
    omega
  have hprod :
      ((Finset.univ.filter (fun i : Fin L => a ≤ i.val)).product
       (Finset.univ.filter (fun i : Fin L => b ≤ i.val))).card =
      (L - a) * (L - b) := by
    rw [Finset.product_eq_sprod, Finset.card_product, hnonA, hnonB]
  rw [hprod] at hcomp
  omega

def linearImage (a b : ℕ) {L : ℕ} (p : Fin L × Fin L) : ℤ :=
  (b : ℤ) * (p.1.val : ℤ) - (a : ℤ) * (p.2.val : ℤ)

private theorem primitive_kernel (a b du dv : ℤ)
    (ha : a ≠ 0) (hab : Int.gcd a b = 1)
    (h : b * du = a * dv) :
    ∃ t : ℤ, du = a * t ∧ dv = b * t := by
  have hdiv : a ∣ du * b := by rw [mul_comm, h]; exact dvd_mul_right a dv
  have hadu : a ∣ du := Int.dvd_of_dvd_mul_left_of_gcd_one hdiv hab
  obtain ⟨t, ht⟩ := hadu
  refine ⟨t, ht, ?_⟩
  have hh : a * (b * t) = a * dv := by
    calc
      a * (b * t) = b * (a * t) := by ring
      _ = b * du := by rw [← ht]
      _ = a * dv := h
  exact (mul_left_cancel₀ ha hh).symm

theorem linearImage_injOn_starts (L a b : ℕ)
    (ha : 0 < a) (hb : 0 < b) (hab : Int.gcd (a : ℤ) (b : ℤ) = 1) :
    Set.InjOn (linearImage a b) (↑(starts L a b) : Set (Fin L × Fin L)) := by
  intro p hp q hq heq
  have hpst : p.1.val < a ∨ p.2.val < b := by simpa [starts, grid, start] using hp
  have hqst : q.1.val < a ∨ q.2.val < b := by simpa [starts, grid, start] using hq
  have hmul : (b : ℤ) * ((p.1.val : ℤ) - q.1.val) =
      (a : ℤ) * ((p.2.val : ℤ) - q.2.val) := by
    dsimp [linearImage] at heq
    nlinarith [heq]
  obtain ⟨t, hdu, hdv⟩ := primitive_kernel (a : ℤ) (b : ℤ)
    ((p.1.val : ℤ) - q.1.val) ((p.2.val : ℤ) - q.2.val)
    (by exact_mod_cast Nat.ne_of_gt ha) hab hmul
  rcases lt_trichotomy t 0 with htneg | htzero | htpos
  · have hta : (a : ℤ) ≤ -(a : ℤ) * t := by
      have hnon : (0 : ℤ) ≤ -t - 1 := by omega
      nlinarith [mul_nonneg (show (0 : ℤ) ≤ a by exact_mod_cast Nat.zero_le a) hnon]
    have htb : (b : ℤ) ≤ -(b : ℤ) * t := by
      have hnon : (0 : ℤ) ≤ -t - 1 := by omega
      nlinarith [mul_nonneg (show (0 : ℤ) ≤ b by exact_mod_cast Nat.zero_le b) hnon]
    have hta' : (a : ℤ) ≤ -((a : ℤ) * t) := by nlinarith [hta]
    have htb' : (b : ℤ) ≤ -((b : ℤ) * t) := by nlinarith [htb]
    omega
  · simp only [htzero, mul_zero] at hdu hdv
    have hpu : p.1 = q.1 := Fin.ext (by omega)
    have hpv : p.2 = q.2 := Fin.ext (by omega)
    exact Prod.ext hpu hpv
  · have hta : (a : ℤ) ≤ (a : ℤ) * t := by
      have hnon : (0 : ℤ) ≤ t - 1 := by omega
      nlinarith [mul_nonneg (show (0 : ℤ) ≤ a by exact_mod_cast Nat.zero_le a) hnon]
    have htb : (b : ℤ) ≤ (b : ℤ) * t := by
      have hnon : (0 : ℤ) ≤ t - 1 := by omega
      nlinarith [mul_nonneg (show (0 : ℤ) ≤ b by exact_mod_cast Nat.zero_le b) hnon]
    omega

theorem exists_start_same_image (L a b : ℕ) (ha : 0 < a) (hb : 0 < b)
    (p : Fin L × Fin L) :
    ∃ q ∈ starts L a b, linearImage a b q = linearImage a b p := by
  suffices h : ∀ n : ℕ, ∀ p : Fin L × Fin L, p.1.val = n →
      ∃ q ∈ starts L a b, linearImage a b q = linearImage a b p from
    h p.1.val p rfl
  intro n
  induction n using Nat.strong_induction_on with
  | h n ih =>
    intro p hp
    by_cases hs : start a b p
    · exact ⟨p, by simp [starts, grid, hs], rfl⟩
    · have hnot : ¬(p.1.val < a ∨ p.2.val < b) := by simpa [start] using hs
      have hpa : a ≤ p.1.val := not_lt.mp (not_or.mp hnot).1
      have hpb : b ≤ p.2.val := not_lt.mp (not_or.mp hnot).2
      let p' : Fin L × Fin L :=
        (⟨p.1.val - a, by omega⟩, ⟨p.2.val - b, by omega⟩)
      have hp'lt : p'.1.val < n := by simp [p']; omega
      have hp'img : linearImage a b p' = linearImage a b p := by
        have hsuba : ((p.1.val - a : ℕ) : ℤ) = (p.1.val : ℤ) - a := by omega
        have hsubb : ((p.2.val - b : ℕ) : ℤ) = (p.2.val : ℤ) - b := by omega
        simp only [linearImage, p', hsuba, hsubb]
        ring
      obtain ⟨q, hq, hqimg⟩ := ih p'.1.val hp'lt p' rfl
      exact ⟨q, hq, hqimg.trans hp'img⟩

theorem image_starts_eq_grid (L a b : ℕ) (ha : 0 < a) (hb : 0 < b) :
    (starts L a b).image (linearImage a b) =
      (grid L).image (linearImage a b) := by
  classical
  ext z
  constructor
  · intro hz
    obtain ⟨p, hp, rfl⟩ := Finset.mem_image.mp hz
    exact Finset.mem_image.mpr ⟨p, Finset.filter_subset _ _ hp, rfl⟩
  · intro hz
    obtain ⟨p, _, rfl⟩ := Finset.mem_image.mp hz
    obtain ⟨q, hq, hqimg⟩ := exists_start_same_image L a b ha hb p
    exact Finset.mem_image.mpr ⟨q, hq, hqimg⟩

theorem integer_grid_image_card (L a b : ℕ)
    (ha : 0 < a) (hb : 0 < b) (hab : Int.gcd (a : ℤ) (b : ℤ) = 1) :
    ((grid L).image (linearImage a b)).card =
      L ^ 2 - (L - a) * (L - b) := by
  rw [← image_starts_eq_grid L a b ha hb]
  exact (Finset.card_image_of_injOn (linearImage_injOn_starts L a b ha hb hab)).trans
    (card_starts L a b)

private theorem zmod_cast_eq_of_interval (q : ℕ) (lo hi z w : ℤ)
    (hwidth : hi - lo < q)
    (hzlo : lo ≤ z) (hzhi : z ≤ hi)
    (hwlo : lo ≤ w) (hwhi : w ≤ hi)
    (heq : (z : ZMod q) = (w : ZMod q)) : z = w := by
  have hd : (q : ℤ) ∣ w - z :=
    (ZMod.intCast_eq_intCast_iff_dvd_sub z w q).mp heq
  have hlt : -(q : ℤ) < w - z ∧ w - z < (q : ℤ) := by omega
  have habs : (w - z).natAbs < (q : ℤ).natAbs := by
    by_cases hp : 0 ≤ w - z
    · exact Int.natAbs_lt_natAbs_of_nonneg_of_lt hp hlt.2
    · have hn : 0 ≤ -(w - z) := by omega
      have hnlt : -(w - z) < (q : ℤ) := by omega
      simpa only [Int.natAbs_neg] using
        (Int.natAbs_lt_natAbs_of_nonneg_of_lt hn hnlt)
  have hzero : w - z = 0 := Int.eq_zero_of_dvd_of_natAbs_lt_natAbs hd habs
  omega

def modImage (q a b : ℕ) {L : ℕ} (p : Fin L × Fin L) : ZMod q :=
  (linearImage a b p : ZMod q)

theorem mod_grid_image_card (H a b q : ℕ)
    (ha : 0 < a) (hb : 0 < b)
    (hab : Int.gcd (a : ℤ) (b : ℤ) = 1)
    (hnowrap : (2 * H) * (a + b) < q) :
    ((grid (2 * H + 1)).image (modImage q a b)).card =
      (2 * H + 1) ^ 2 - ((2 * H + 1) - a) * ((2 * H + 1) - b) := by
  classical
  let L := 2 * H + 1
  let values := (grid L).image (linearImage a b)
  have hbound (p : Fin L × Fin L) :
      -(a : ℤ) * (2 * H : ℤ) ≤ linearImage a b p ∧
        linearImage a b p ≤ (b : ℤ) * (2 * H : ℤ) := by
    have hu : (p.1.val : ℤ) ≤ (2 * H : ℤ) := by omega
    have hv : (p.2.val : ℤ) ≤ (2 * H : ℤ) := by omega
    have hbu : (b : ℤ) * (p.1.val : ℤ) ≤ (b : ℤ) * (2 * H : ℤ) :=
      mul_le_mul_of_nonneg_left hu (by exact_mod_cast Nat.zero_le b)
    have hav : (a : ℤ) * (p.2.val : ℤ) ≤ (a : ℤ) * (2 * H : ℤ) :=
      mul_le_mul_of_nonneg_left hv (by exact_mod_cast Nat.zero_le a)
    dsimp [linearImage]
    constructor <;> nlinarith [mul_nonneg (show (0 : ℤ) ≤ b by exact_mod_cast Nat.zero_le b)
      (show (0 : ℤ) ≤ p.1.val by exact_mod_cast Nat.zero_le p.1.val),
      mul_nonneg (show (0 : ℤ) ≤ a by exact_mod_cast Nat.zero_le a)
      (show (0 : ℤ) ≤ p.2.val by exact_mod_cast Nat.zero_le p.2.val)]
  have hinj : Set.InjOn (fun z : ℤ => (z : ZMod q)) (↑values : Set ℤ) := by
    intro z hz w hw heq
    obtain ⟨p, _, rfl⟩ := Finset.mem_image.mp hz
    obtain ⟨p', _, rfl⟩ := Finset.mem_image.mp hw
    have hwid : (b : ℤ) * (2 * H : ℤ) - (-(a : ℤ) * (2 * H : ℤ)) < q := by
      have hc : (((2 * H) * (a + b) : ℕ) : ℤ) < q := by exact_mod_cast hnowrap
      nlinarith [hc]
    exact zmod_cast_eq_of_interval q _ _ _ _ hwid
      (hbound p).1 (hbound p).2 (hbound p').1 (hbound p').2 heq
  have himg : (grid L).image (modImage q a b) = values.image (fun z : ℤ => (z : ZMod q)) := by
    dsimp [values, modImage]
    rw [Finset.image_image]
    rfl
  rw [himg, Finset.card_image_of_injOn hinj]
  exact integer_grid_image_card L a b ha hb hab

def centeredModImage (q H a b : ℕ)
    (p : Fin (2 * H + 1) × Fin (2 * H + 1)) : ZMod q :=
  (((b : ℤ) * ((p.1.val : ℤ) - H) -
      (a : ℤ) * ((p.2.val : ℤ) - H) : ℤ) : ZMod q)

theorem centered_mod_grid_image_card (H a b q : ℕ)
    (ha : 0 < a) (hb : 0 < b)
    (hab : Int.gcd (a : ℤ) (b : ℤ) = 1)
    (hnowrap : (2 * H) * (a + b) < q) :
    ((grid (2 * H + 1)).image (centeredModImage q H a b)).card =
      (2 * H + 1) ^ 2 - ((2 * H + 1) - a) * ((2 * H + 1) - b) := by
  classical
  let c : ZMod q := (((a : ℤ) - b) * H : ℤ)
  have hfun (p : Fin (2 * H + 1) × Fin (2 * H + 1)) :
      centeredModImage q H a b p = modImage q a b p + c := by
    have hint :
        (b : ℤ) * ((p.1.val : ℤ) - H) - (a : ℤ) * ((p.2.val : ℤ) - H) =
        linearImage a b p + ((a : ℤ) - b) * H := by
      dsimp [linearImage]
      ring
    dsimp [centeredModImage, modImage, c]
    rw [hint, Int.cast_add]
  have himg : (grid (2 * H + 1)).image (centeredModImage q H a b) =
      ((grid (2 * H + 1)).image (modImage q a b)).image (fun z => z + c) := by
    rw [Finset.image_image]
    congr 1
    funext p
    exact hfun p
  have htrans :
      (((grid (2 * H + 1)).image (modImage q a b)).image (fun z => z + c)).card =
        ((grid (2 * H + 1)).image (modImage q a b)).card := by
    exact Finset.card_image_of_injOn (fun _ _ _ _ heq => add_right_cancel heq)
  rw [himg, htrans]
  exact mod_grid_image_card H a b q ha hb hab hnowrap

def reflectFirst {L : ℕ} (p : Fin L × Fin L) : Fin L × Fin L :=
  (p.1.rev, p.2)

theorem reflectFirst_involutive (L : ℕ) :
    Function.Involutive (reflectFirst (L := L)) := by
  intro p
  ext <;> simp [reflectFirst, Fin.rev_rev]

def centeredNegativeModImage (q H a b : ℕ)
    (p : Fin (2 * H + 1) × Fin (2 * H + 1)) : ZMod q :=
  (((-(b : ℤ)) * ((p.1.val : ℤ) - H) -
      (a : ℤ) * ((p.2.val : ℤ) - H) : ℤ) : ZMod q)

theorem centered_negative_mod_grid_image_card (H a b q : ℕ)
    (ha : 0 < a) (hb : 0 < b)
    (hab : Int.gcd (a : ℤ) (b : ℤ) = 1)
    (hnowrap : (2 * H) * (a + b) < q) :
    ((grid (2 * H + 1)).image (centeredNegativeModImage q H a b)).card =
      (2 * H + 1) ^ 2 - ((2 * H + 1) - a) * ((2 * H + 1) - b) := by
  classical
  let L := 2 * H + 1
  have hfun (p : Fin L × Fin L) :
      centeredNegativeModImage q H a b p =
        centeredModImage q H a b (reflectFirst p) := by
    have hrev : ((p.1.rev.val : ℤ) - H) = -((p.1.val : ℤ) - H) := by
      simp only [Fin.val_rev]
      omega
    have hint :
        -(b : ℤ) * ((p.1.val : ℤ) - H) - (a : ℤ) * ((p.2.val : ℤ) - H) =
        (b : ℤ) * ((p.1.rev.val : ℤ) - H) - (a : ℤ) * ((p.2.val : ℤ) - H) := by
      rw [hrev]
      ring
    exact congrArg (fun z : ℤ => (z : ZMod q)) hint
  have himg : (grid L).image (centeredNegativeModImage q H a b) =
      (grid L).image (fun p => centeredModImage q H a b (reflectFirst p)) := by
    congr 1
    funext p
    exact hfun p
  have hperm : (grid L).image (fun p => centeredModImage q H a b (reflectFirst p)) =
      (grid L).image (centeredModImage q H a b) := by
    ext z
    simp only [grid, Finset.mem_image, Finset.mem_univ, true_and]
    constructor
    · rintro ⟨p, rfl⟩
      exact ⟨reflectFirst p, rfl⟩
    · rintro ⟨p, rfl⟩
      exact ⟨reflectFirst p, by rw [reflectFirst_involutive]⟩
  rw [himg, hperm]
  exact centered_mod_grid_image_card H a b q ha hb hab hnowrap

#print axioms card_starts
#print axioms linearImage_injOn_starts
#print axioms exists_start_same_image
#print axioms image_starts_eq_grid
#print axioms integer_grid_image_card
#print axioms mod_grid_image_card
#print axioms centered_mod_grid_image_card
#print axioms reflectFirst_involutive
#print axioms centered_negative_mod_grid_image_card

end XedniGridCardinality
