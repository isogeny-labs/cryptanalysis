import Std

/-! Structural soundness of the exact nine-link balanced ten-point tree.
The field-coordinate slope equations and their chart exceptional cases are
the explicit `link_sound` obligation; see PROOF_MAP.md. -/

namespace N41FullPointTree

universe u
variable {Point : Type u}

theorem nine_link_sound
    (nodes : Fin 19 → Point)
    (link : Point → Point → Point → Prop)
    (sum : Point → Point → Point)
    (link_sound : ∀ a b c, link a b c → c = sum a b)
    (h10 : link (nodes 0) (nodes 1) (nodes 10))
    (h11 : link (nodes 2) (nodes 3) (nodes 11))
    (h12 : link (nodes 4) (nodes 5) (nodes 12))
    (h13 : link (nodes 6) (nodes 7) (nodes 13))
    (h14 : link (nodes 10) (nodes 11) (nodes 14))
    (h15 : link (nodes 12) (nodes 13) (nodes 15))
    (h16 : link (nodes 14) (nodes 15) (nodes 16))
    (h17 : link (nodes 16) (nodes 8) (nodes 17))
    (h18 : link (nodes 17) (nodes 9) (nodes 18)) :
    nodes 18 =
      sum (sum
        (sum
          (sum (sum (nodes 0) (nodes 1)) (sum (nodes 2) (nodes 3)))
          (sum (sum (nodes 4) (nodes 5)) (sum (nodes 6) (nodes 7))))
        (nodes 8)) (nodes 9) := by
  have e10 := link_sound _ _ _ h10
  have e11 := link_sound _ _ _ h11
  have e12 := link_sound _ _ _ h12
  have e13 := link_sound _ _ _ h13
  have e14 := link_sound _ _ _ h14
  have e15 := link_sound _ _ _ h15
  have e16 := link_sound _ _ _ h16
  have e17 := link_sound _ _ _ h17
  have e18 := link_sound _ _ _ h18
  rw [e18, e17, e16, e14, e15, e10, e11, e12, e13]

#print axioms N41FullPointTree.nine_link_sound

end N41FullPointTree
