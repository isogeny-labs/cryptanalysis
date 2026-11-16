import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Int.Interval
import Mathlib.Tactic

namespace XedniCoefficientHoldout

/-- The coefficient vectors were fixed by the earlier training-panel protocol. -/
def family : Finset (ℤ × ℤ) :=
  {(1,-3), (1,-2), (1,-1), (1,1), (1,2), (1,3),
   (2,-3), (2,-1), (2,1), (2,3),
   (3,-2), (3,-1), (3,1), (3,2)}

/-- Indexed in the frozen lexicographic test order. -/
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

theorem vector_image_eq_family : Finset.univ.image vector = family := by decide

/-- The public relation equation at `t₁=0`, `Q=17G`, and second offset `t`. -/
def equation (q : ℕ) (c : ℤ × ℤ) (t : ℕ) : Prop :=
  (((c.1 + c.2) * 17 - c.2 * (t : ℤ) : ℤ) : ZMod q) = 0

/-- The vector `(1,1)` relates at offset 34 for every modulus. -/
theorem relation_at_34 (q : ℕ) : equation q (1,1) 34 := by
  simp [equation]

theorem no_relation_before_34_751 :
    ∀ t : Fin 34, t.val ≠ 0 → t.val ≠ 17 →
      ∀ j : Fin 14, ¬ equation 751 (vector j) t.val := by
  unfold equation
  decide

theorem no_relation_before_34_883 :
    ∀ t : Fin 34, t.val ≠ 0 → t.val ≠ 17 →
      ∀ j : Fin 14, ¬ equation 883 (vector j) t.val := by
  unfold equation
  decide

theorem no_relation_before_34_983 :
    ∀ t : Fin 34, t.val ≠ 0 → t.val ≠ 17 →
      ∀ j : Fin 14, ¬ equation 983 (vector j) t.val := by
  unfold equation
  decide

theorem no_relation_before_34_1103 :
    ∀ t : Fin 34, t.val ≠ 0 → t.val ≠ 17 →
      ∀ j : Fin 14, ¬ equation 1103 (vector j) t.val := by
  unfold equation
  decide

theorem no_relation_before_34_1153 :
    ∀ t : Fin 34, t.val ≠ 0 → t.val ≠ 17 →
      ∀ j : Fin 14, ¬ equation 1153 (vector j) t.val := by
  unfold equation
  decide

theorem no_relation_before_34_1453 :
    ∀ t : Fin 34, t.val ≠ 0 → t.val ≠ 17 →
      ∀ j : Fin 14, ¬ equation 1453 (vector j) t.val := by
  unfold equation
  decide

theorem no_relation_before_34_1459 :
    ∀ t : Fin 34, t.val ≠ 0 → t.val ≠ 17 →
      ∀ j : Fin 14, ¬ equation 1459 (vector j) t.val := by
  unfold equation
  decide

#print axioms vector_image_eq_family
#print axioms relation_at_34
#print axioms no_relation_before_34_751
#print axioms no_relation_before_34_883
#print axioms no_relation_before_34_983
#print axioms no_relation_before_34_1103
#print axioms no_relation_before_34_1153
#print axioms no_relation_before_34_1453
#print axioms no_relation_before_34_1459

end XedniCoefficientHoldout
