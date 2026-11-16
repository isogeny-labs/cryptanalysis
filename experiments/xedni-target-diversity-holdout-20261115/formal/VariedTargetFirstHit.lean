import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Int.Interval
import Mathlib.Tactic

set_option maxRecDepth 10000
set_option maxHeartbeats 0

namespace XedniVariedTarget

/-- Frozen coefficient test order from the training protocol. -/
def vector (j : Fin 14) : ℤ × ℤ :=
  match j.val with
  | 0 => (1,-3)
  | 1 => (1,-2)
  | 2 => (1,-1)
  | 3 => (1,1)
  | 4 => (1,2)
  | 5 => (1,3)
  | 6 => (2,-3)
  | 7 => (2,-1)
  | 8 => (2,1)
  | 9 => (2,3)
  | 10 => (3,-2)
  | 11 => (3,-1)
  | 12 => (3,1)
  | _ => (3,2)

/-- Group relation equation for Q=dG, R₁=Q, and R₂=Q-tG in a group of order q. -/
def equation (q d : ℕ) (c : ℤ × ℤ) (t : ℕ) : Prop :=
  (((c.1 + c.2) * (d : ℤ) - c.2 * (t : ℤ) : ℤ) : ZMod q) = 0

theorem relation_at_hit_773 : equation 751 496 (vector ⟨3, by decide⟩) 241 := by
  unfold equation
  decide

theorem no_relation_before_hit_773 :
    ∀ t : Fin 241, t.val ≠ 0 → t.val ≠ 496 →
      ∀ j : Fin 14, ¬ equation 751 496 (vector j) t.val := by
  unfold equation
  decide

theorem relation_at_hit_863 : equation 883 671 (vector ⟨12, by decide⟩) 35 := by
  unfold equation
  decide

theorem no_relation_before_hit_863 :
    ∀ t : Fin 35, t.val ≠ 0 → t.val ≠ 671 →
      ∀ j : Fin 14, ¬ equation 883 671 (vector j) t.val := by
  unfold equation
  decide

theorem relation_at_hit_883 : equation 883 260 (vector ⟨1, by decide⟩) 130 := by
  unfold equation
  decide

theorem no_relation_before_hit_883 :
    ∀ t : Fin 130, t.val ≠ 0 → t.val ≠ 260 →
      ∀ j : Fin 14, ¬ equation 883 260 (vector j) t.val := by
  unfold equation
  decide

theorem relation_at_hit_983 : equation 983 671 (vector ⟨8, by decide⟩) 47 := by
  unfold equation
  decide

theorem no_relation_before_hit_983 :
    ∀ t : Fin 47, t.val ≠ 0 → t.val ≠ 671 →
      ∀ j : Fin 14, ¬ equation 983 671 (vector j) t.val := by
  unfold equation
  decide

theorem relation_at_hit_1049 : equation 1103 775 (vector ⟨8, by decide⟩) 119 := by
  unfold equation
  decide

theorem no_relation_before_hit_1049 :
    ∀ t : Fin 119, t.val ≠ 0 → t.val ≠ 775 →
      ∀ j : Fin 14, ¬ equation 1103 775 (vector j) t.val := by
  unfold equation
  decide

theorem relation_at_hit_1153 : equation 1153 530 (vector ⟨11, by decide⟩) 93 := by
  unfold equation
  decide

theorem no_relation_before_hit_1153 :
    ∀ t : Fin 93, t.val ≠ 0 → t.val ≠ 530 →
      ∀ j : Fin 14, ¬ equation 1153 530 (vector j) t.val := by
  unfold equation
  decide

theorem relation_at_hit_1423 : equation 1453 342 (vector ⟨6, by decide⟩) 114 := by
  unfold equation
  decide

theorem no_relation_before_hit_1423 :
    ∀ t : Fin 114, t.val ≠ 0 → t.val ≠ 342 →
      ∀ j : Fin 14, ¬ equation 1453 342 (vector j) t.val := by
  unfold equation
  decide

theorem relation_at_hit_1433 : equation 1459 430 (vector ⟨5, by decide⟩) 87 := by
  unfold equation
  decide

theorem no_relation_before_hit_1433 :
    ∀ t : Fin 87, t.val ≠ 0 → t.val ≠ 430 →
      ∀ j : Fin 14, ¬ equation 1459 430 (vector j) t.val := by
  unfold equation
  decide

#print axioms relation_at_hit_773
#print axioms no_relation_before_hit_773
#print axioms relation_at_hit_863
#print axioms no_relation_before_hit_863
#print axioms relation_at_hit_883
#print axioms no_relation_before_hit_883
#print axioms relation_at_hit_983
#print axioms no_relation_before_hit_983
#print axioms relation_at_hit_1049
#print axioms no_relation_before_hit_1049
#print axioms relation_at_hit_1153
#print axioms no_relation_before_hit_1153
#print axioms relation_at_hit_1423
#print axioms no_relation_before_hit_1423
#print axioms relation_at_hit_1433
#print axioms no_relation_before_hit_1433

end XedniVariedTarget
