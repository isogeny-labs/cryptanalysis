module

public import Init

namespace ProjectionP1277

public theorem signed_triple_residue_nonzero :
    ∀ a b c : Fin 2,
      ((if a.val = 0 then (1 : Fin 5) else 4) +
       (if b.val = 0 then (1 : Fin 5) else 4) +
       (if c.val = 0 then (1 : Fin 5) else 4)) ≠ 0 := by decide

public theorem no_three_in_opposite_cosets
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

public theorem mixed_source_residues_allow_zero :
    (2 : Fin 5) + 4 + 4 = 0 ∧ (3 : Fin 5) + 1 + 1 = 0 := by decide

#print axioms signed_triple_residue_nonzero
#print axioms no_three_in_opposite_cosets
#print axioms mixed_source_residues_allow_zero

end ProjectionP1277
