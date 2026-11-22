import Std

/-! The eight circuit links compute the same nine-point sum as a serial chain
whenever the underlying point addition is associative. The SAT encoding of
each link and its exceptional-coordinate exclusions are checked separately. -/
namespace BalancedTree

universe u
variable {G : Type u}

theorem nine_sum_eq_serial (add : G → G → G)
    (hassoc : ∀ x y z, add (add x y) z = add x (add y z))
    (a b c d e f g h i : G) :
    add (add (add (add (add (add (add (add a b) c) d) e) f) g) h) i =
      add (add (add (add a b) (add c d)) (add (add e f) (add g h))) i := by
  simp only [hassoc]

#print axioms BalancedTree.nine_sum_eq_serial

end BalancedTree
