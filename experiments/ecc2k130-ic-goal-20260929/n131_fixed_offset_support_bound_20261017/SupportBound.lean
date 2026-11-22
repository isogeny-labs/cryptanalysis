import Std

namespace SupportBound

def tuples {α : Type} (states : List α) : Nat → List (List α)
  | 0 => [[]]
  | n + 1 => states.flatMap fun x => (tuples states n).map (x :: ·)

private theorem flatMap_cons_length {α : Type} (xs : List α)
    (ys : List (List α)) :
    (xs.flatMap fun x => ys.map (x :: ·)).length = xs.length * ys.length := by
  induction xs with
  | nil => simp
  | cons x xs ih => simp [ih, Nat.succ_mul, Nat.add_comm]

theorem tuples_length {α : Type} (states : List α) (m : Nat) :
    (tuples states m).length = states.length ^ m := by
  induction m with
  | zero => simp [tuples]
  | succ m ih =>
      rw [tuples, flatMap_cons_length, ih]
      simp [Nat.pow_succ, Nat.mul_comm]

theorem seven_slot_capacity_below_group (covered : Nat)
    (h : covered ≤ (4 * 33191) ^ 7) :
    covered < 680564733841876926932320129493409985129 := by
  exact Nat.lt_of_le_of_lt h (by decide)

theorem eight_slot_capacity_reaches_group :
    680564733841876926932320129493409985129 ≤ (4 * 33191) ^ 8 := by
  decide

#print axioms tuples_length
#print axioms seven_slot_capacity_below_group
#print axioms eight_slot_capacity_reaches_group

end SupportBound
