import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Finset.Card
import Mathlib.Tactic

namespace XedniAdaptiveCollision

structure Affine (F : Type*) where
  slope : F
  intercept : F
deriving DecidableEq

def eval {F : Type*} [Ring F] (f : Affine F) (w : F) : F :=
  f.slope * w + f.intercept

def candidate {F : Type*} [DivisionRing F] (f g : Affine F) : F :=
  (g.intercept - f.intercept) / (f.slope - g.slope)

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

theorem public_group_collision_iff {F A : Type*} [Field F]
    [AddCommGroup A] [Module F A] (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (f g : Affine F) (w : F) :
    (eval f w) • G = (eval g w) • G ↔ eval f w = eval g w := by
  exact ⟨fun h => hinj h, fun h => by rw [h]⟩

/-- Before the first informative collision, every answer in the Boolean
history is false, so there is only one possible history of each length. -/
theorem miss_history_unique (history : List Bool)
    (h : ∀ b ∈ history, b = false) :
    history = List.replicate history.length false := by
  induction history with
  | nil => rfl
  | cons b tail ih =>
      have hb : b = false := h b (by simp)
      have ht : ∀ x ∈ tail, x = false := by
        intro x hx
        exact h x (by simp [hx])
      subst b
      calc
        false :: tail = false :: List.replicate tail.length false :=
          congrArg (List.cons false) (ih ht)
        _ = List.replicate (false :: tail).length false := by
          simp only [List.length_cons, List.replicate_succ]

theorem prehit_strategy_fixed {F : Type*} (strategy : List Bool → Affine F)
    (history : List Bool) (h : ∀ b ∈ history, b = false) :
    strategy history = strategy (List.replicate history.length false) := by
  exact congrArg strategy (miss_history_unique history h)

def negativeForm {F : Type*} (strategy : List Bool → Affine F) (i : ℕ) : Affine F :=
  strategy (List.replicate i false)

noncomputable def activePairs {F : Type*} [DecidableEq F] {n : ℕ}
    (strategy : List Bool → Affine F) : Finset (Fin n × Fin n) := by
  classical
  exact (Finset.univ.product Finset.univ).filter
    (fun ij => ij.1 < ij.2 ∧
      (negativeForm strategy ij.1).slope ≠ (negativeForm strategy ij.2).slope)

def informativeCollision {F : Type*} [Ring F]
    (f g : Affine F) (w : F) : Prop :=
  f.slope ≠ g.slope ∧ eval f w = eval g w

noncomputable def successSet {F : Type*} [Fintype F] [DecidableEq F]
    [Field F] {n : ℕ} (strategy : List Bool → Affine F) : Finset F := by
  classical
  exact Finset.univ.filter (fun w =>
    ∃ ij ∈ activePairs (n := n) strategy,
      informativeCollision (negativeForm strategy ij.1)
        (negativeForm strategy ij.2) w)

theorem collision_iff_candidate {F : Type*} [Field F]
    (f g : Affine F) (hs : f.slope ≠ g.slope) (w : F) :
    informativeCollision f g w ↔ w = candidate f g := by
  have hd : f.slope - g.slope ≠ 0 := sub_ne_zero.mpr hs
  unfold informativeCollision eval candidate
  constructor
  · rintro ⟨_, heq⟩
    apply (eq_div_iff hd).2
    linear_combination heq
  · intro heq
    refine ⟨hs, ?_⟩
    apply (eq_div_iff hd).1 at heq
    linear_combination heq

theorem adaptive_collision_success_set {F : Type*} [Fintype F]
    [DecidableEq F] [Field F] {n : ℕ}
    (strategy : List Bool → Affine F) :
    successSet (n := n) strategy =
      (activePairs (n := n) strategy).image
        (fun ij => candidate (negativeForm strategy ij.1)
          (negativeForm strategy ij.2)) := by
  classical
  ext w
  simp only [successSet, Finset.mem_filter, Finset.mem_univ, true_and,
    Finset.mem_image]
  constructor
  · rintro ⟨ij, hij, heq⟩
    have hs : (negativeForm strategy ij.1).slope ≠
        (negativeForm strategy ij.2).slope := (Finset.mem_filter.mp hij).2.2
    exact ⟨ij, hij,
      ((collision_iff_candidate (negativeForm strategy ij.1)
        (negativeForm strategy ij.2) hs w).mp heq).symm⟩
  · rintro ⟨ij, hij, hc⟩
    have hs : (negativeForm strategy ij.1).slope ≠
        (negativeForm strategy ij.2).slope := (Finset.mem_filter.mp hij).2.2
    exact ⟨ij, hij,
      (collision_iff_candidate (negativeForm strategy ij.1)
        (negativeForm strategy ij.2) hs w).mpr hc.symm⟩

theorem adaptive_collision_card_le_pairs {F : Type*} [Fintype F]
    [DecidableEq F] [Field F] {n : ℕ}
    (strategy : List Bool → Affine F) :
    (successSet (n := n) strategy).card ≤
      (activePairs (n := n) strategy).card := by
  rw [adaptive_collision_success_set]
  exact Finset.card_image_le

theorem adaptive_collision_card_le_square {F : Type*} [Fintype F]
    [DecidableEq F] [Field F] {n : ℕ}
    (strategy : List Bool → Affine F) :
    (successSet (n := n) strategy).card ≤ n * n := by
  calc
    (successSet (n := n) strategy).card
      ≤ (activePairs (n := n) strategy).card :=
        adaptive_collision_card_le_pairs strategy
    _ ≤ (Finset.univ.product (Finset.univ : Finset (Fin n))).card :=
      Finset.card_le_card (Finset.filter_subset _ _)
    _ = n * n := by simp

#print axioms miss_history_unique
#print axioms prehit_strategy_fixed
#print axioms same_slope_distinct_ne
#print axioms public_group_collision_iff
#print axioms collision_iff_candidate
#print axioms adaptive_collision_success_set
#print axioms adaptive_collision_card_le_pairs
#print axioms adaptive_collision_card_le_square

end XedniAdaptiveCollision
