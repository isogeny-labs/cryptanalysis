module

public import Init

namespace CosetPanel

public theorem no_three_in_antipodal_class
    {G : Type} (zero : G) (add : G → G → G) (proj : G → Fin 5)
    (hzero : proj zero = 0)
    (hadd : ∀ x y, proj (add x y) = proj x + proj y)
    (a b c : G)
    (ha : proj a = 1 ∨ proj a = 4)
    (hb : proj b = 1 ∨ proj b = 4)
    (hc : proj c = 1 ∨ proj c = 4) :
    add (add a b) c ≠ zero := by
  intro heq
  have hsum : proj a + proj b + proj c = (0 : Fin 5) := by
    calc
      proj a + proj b + proj c = proj (add (add a b) c) := by rw [hadd, hadd]
      _ = proj zero := by rw [heq]
      _ = 0 := hzero
  rcases ha with ha | ha <;> rcases hb with hb | hb <;> rcases hc with hc | hc <;>
    simp [ha, hb, hc] at hsum

public theorem eight_frozen_projection_summaries :
    ([20, 20, 0, 0, 0] : List Nat).sum = 40 ∧
    ([0, 20, 20, 0, 0] : List Nat).sum = 40 ∧
    ([0, 20, 20, 0, 0] : List Nat).sum = 40 ∧
    ([0, 20, 20, 0, 0] : List Nat).sum = 40 ∧
    ([0, 20, 20, 0, 0] : List Nat).sum = 40 ∧
    ([0, 40, 0, 0, 0] : List Nat).sum = 40 ∧
    ([20, 20, 0, 0, 0] : List Nat).sum = 40 ∧
    ([0, 20, 0, 0, 20] : List Nat).sum = 40 := by decide

public theorem opposite_residues_block_three :
    ∀ a b c : Fin 2,
      ((if a.val = 0 then (1 : Fin 5) else 4) +
       (if b.val = 0 then (1 : Fin 5) else 4) +
       (if c.val = 0 then (1 : Fin 5) else 4)) ≠ 0 := by decide

public theorem mixed_residues_can_cancel :
    (1 : Fin 5) + 2 + 2 = 0 ∧
    (0 : Fin 5) + 1 + 4 = 0 := by decide

#print axioms no_three_in_antipodal_class
#print axioms eight_frozen_projection_summaries
#print axioms opposite_residues_block_three
#print axioms mixed_residues_can_cancel

end CosetPanel
