import Std

/-! The ten free pair outputs are combined in the exact nine-link order
used by `tenpair.py`. The final link places the fifth pair before the
first four pairs, so commutativity as well as associativity is required. -/
namespace BalancedTen

universe u

theorem ten_sum_eq_serial {G : Type u} (add : G → G → G)
    (hassoc : ∀ x y z, add (add x y) z = add x (add y z))
    (hcomm : ∀ x y, add x y = add y x)
    (a b c d e f g h i j : G) :
    add (add (add (add (add (add (add (add (add a b) c) d) e) f) g) h) i) j =
      add (add (add i j) (add (add a b) (add c d)))
        (add (add e f) (add g h)) := by
  have hrotate (x y z : G) : add (add x y) z = add (add y z) x := by
    rw [hassoc, hcomm x (add y z)]
  calc
    add (add (add (add (add (add (add (add (add a b) c) d) e) f) g) h) i) j =
        add (add
          (add (add (add a b) (add c d)) (add (add e f) (add g h)))
          i) j := by simp only [hassoc]
    _ = add
          (add (add (add a b) (add c d)) (add (add e f) (add g h)))
          (add i j) := by rw [hassoc]
    _ = add (add (add i j) (add (add a b) (add c d)))
          (add (add e f) (add g h)) :=
          (hrotate (add i j) (add (add a b) (add c d))
            (add (add e f) (add g h))).symm

#print axioms BalancedTen.ten_sum_eq_serial

end BalancedTen
