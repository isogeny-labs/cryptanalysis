import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Finset.Card
import Mathlib.Tactic

namespace XedniSymbolicCollision

structure Affine (F : Type*) where
  slope : F
  intercept : F
deriving DecidableEq

def eval {F : Type*} [Ring F] (f : Affine F) (w : F) : F :=
  f.slope * w + f.intercept

def plus {F : Type*} [Add F] (f g : Affine F) : Affine F :=
  ⟨f.slope + g.slope, f.intercept + g.intercept⟩

def scale {F : Type*} [Ring F] (c : F) (f : Affine F) : Affine F :=
  ⟨c * f.slope, c * f.intercept⟩

theorem eval_plus {F : Type*} [CommRing F] (f g : Affine F) (w : F) :
    eval (plus f g) w = eval f w + eval g w := by
  simp [eval, plus, add_mul]
  abel

theorem eval_scale {F : Type*} [CommRing F] (c : F) (f : Affine F) (w : F) :
    eval (scale c f) w = c * eval f w := by
  simp [eval, scale, mul_add, mul_assoc]

def candidate {F : Type*} [DivisionRing F] (f g : Affine F) : F :=
  (g.intercept - f.intercept) / (f.slope - g.slope)

theorem unequal_slope_eq_iff_candidate {F : Type*} [Field F]
    (f g : Affine F) (h : f.slope ≠ g.slope) (w : F) :
    eval f w = eval g w ↔ w = candidate f g := by
  have hd : f.slope - g.slope ≠ 0 := sub_ne_zero.mpr h
  unfold eval candidate
  constructor
  · intro heq
    apply (eq_div_iff hd).2
    linear_combination heq
  · intro heq
    apply (eq_div_iff hd).1 at heq
    linear_combination heq

theorem same_slope_distinct_ne {F : Type*} [Field F]
    (f g : Affine F) (hs : f.slope = g.slope) (hfg : f ≠ g) (w : F) :
    eval f w ≠ eval g w := by
  have hi : f.intercept ≠ g.intercept := by
    intro heq
    apply hfg
    cases f
    cases g
    simp_all
  simp [eval, hs, hi]

theorem public_group_equality_iff {F A : Type*} [Field F]
    [AddCommGroup A] [Module F A] (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (f g : Affine F) (w : F) :
    (eval f w) • G = (eval g w) • G ↔ eval f w = eval g w := by
  exact ⟨fun h => hinj h, fun h => by rw [h]⟩

def activePairs {F : Type*} [DecidableEq F]
    [DecidableRel (· ≠ · : F → F → Prop)] {n : ℕ}
    (forms : Fin n → Affine F) : Finset (Fin n × Fin n) :=
  (Finset.univ.product Finset.univ).filter
    (fun ij => ij.1 < ij.2 ∧ (forms ij.1).slope ≠ (forms ij.2).slope)

noncomputable def collisionSet {F : Type*} [Fintype F] [DecidableEq F] [Field F]
    {n : ℕ} (forms : Fin n → Affine F) : Finset F := by
  classical
  exact Finset.univ.filter (fun w =>
    ∃ ij ∈ activePairs forms, eval (forms ij.1) w = eval (forms ij.2) w)

theorem collision_set_eq_candidates {F : Type*} [Fintype F] [DecidableEq F]
    [Field F] {n : ℕ} (forms : Fin n → Affine F) :
    collisionSet forms = (activePairs forms).image
      (fun ij => candidate (forms ij.1) (forms ij.2)) := by
  classical
  ext w
  simp only [collisionSet, Finset.mem_filter, Finset.mem_univ, true_and,
    Finset.mem_image]
  constructor
  · rintro ⟨ij, hij, heq⟩
    have hs : (forms ij.1).slope ≠ (forms ij.2).slope :=
      (Finset.mem_filter.mp hij).2.2
    exact ⟨ij, hij,
      ((unequal_slope_eq_iff_candidate (forms ij.1) (forms ij.2) hs w).mp heq).symm⟩
  · rintro ⟨ij, hij, hc⟩
    have hs : (forms ij.1).slope ≠ (forms ij.2).slope :=
      (Finset.mem_filter.mp hij).2.2
    exact ⟨ij, hij,
      (unequal_slope_eq_iff_candidate (forms ij.1) (forms ij.2) hs w).mpr hc.symm⟩

theorem symbolic_collision_bound {F : Type*} [Fintype F] [DecidableEq F]
    [Field F] {n : ℕ} (forms : Fin n → Affine F) :
    (collisionSet forms).card ≤ n * n := by
  rw [collision_set_eq_candidates]
  calc
    ((activePairs forms).image
      (fun ij => candidate (forms ij.1) (forms ij.2))).card
        ≤ (activePairs forms).card := Finset.card_image_le
    _ ≤ (Finset.univ.product (Finset.univ : Finset (Fin n))).card :=
      Finset.card_le_card (Finset.filter_subset _ _)
    _ = n * n := by simp

theorem collision_card_le_active_pairs {F : Type*} [Fintype F] [DecidableEq F]
    [Field F] {n : ℕ} (forms : Fin n → Affine F) :
    (collisionSet forms).card ≤ (activePairs forms).card := by
  rw [collision_set_eq_candidates]
  exact Finset.card_image_le

#print axioms unequal_slope_eq_iff_candidate
#print axioms eval_plus
#print axioms eval_scale
#print axioms same_slope_distinct_ne
#print axioms public_group_equality_iff
#print axioms collision_set_eq_candidates
#print axioms symbolic_collision_bound
#print axioms collision_card_le_active_pairs

end XedniSymbolicCollision
