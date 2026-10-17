import Std
import Init.Grind.Ring.Basic

namespace DualTree
open Lean.Grind
open Lean.Grind.AddCommMonoid

/-- Both overlapping association trees combine the same six group inputs. -/
theorem same_sum {A : Type} [AddCommGroup A] (a b c d e f : A) :
    ((a + b) + (c + d)) + (e + f) =
      ((a + d) + (b + e)) + (c + f) := by
  have left_comm (x y z : A) : x + (y + z) = y + (x + z) := by
    rw [← add_assoc, add_comm x y, add_assoc]
  simp only [left_comm, add_comm]

#print axioms DualTree.same_sum

end DualTree
