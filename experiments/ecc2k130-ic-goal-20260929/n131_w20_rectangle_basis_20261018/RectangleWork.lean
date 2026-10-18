import Std

/-! A coordinate partition changes the number of nonempty rectangles but not
the number of ordered source-pair assignments those rectangles contain. -/
namespace RectangleWork

theorem row_sum (a : Nat) (ys : List Nat) :
    (ys.map fun b => a * b).sum = a * ys.sum := by
  induction ys with
  | nil => simp
  | cons b rest ih => simp [ih, Nat.mul_add]

theorem ordered_pair_work (xs ys : List Nat) :
    (xs.map fun a => (ys.map fun b => a * b).sum).sum = xs.sum * ys.sum := by
  induction xs with
  | nil => simp
  | cons a rest ih =>
      simp only [List.map_cons, List.sum_cons]
      rw [row_sum a ys, ih, Nat.add_mul]

theorem same_slot_pair_work (counts : List Nat) (source_size : Nat)
    (h : counts.sum = source_size) :
    (counts.map fun a => (counts.map fun b => a * b).sum).sum =
      source_size * source_size := by
  simpa [h] using ordered_pair_work counts counts

#print axioms RectangleWork.row_sum
#print axioms RectangleWork.ordered_pair_work
#print axioms RectangleWork.same_slot_pair_work
end RectangleWork
