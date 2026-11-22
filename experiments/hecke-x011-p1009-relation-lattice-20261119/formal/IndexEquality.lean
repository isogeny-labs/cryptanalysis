import Mathlib
set_option linter.style.haveILetI false

namespace X011RelationLattice

/-- If a row lattice consists of genuine relations, maps onto the finite
group through the ambient free group, and has the same index as the group
order, it is the entire relation kernel. -/
theorem equals_relation_kernel_of_index
    {A B : Type*} [AddGroup A] [AddGroup B] [Finite B]
    (pointMap : A →+ B) (rowLattice : AddSubgroup A)
    (hrows : rowLattice ≤ pointMap.ker)
    (hsurj : Function.Surjective pointMap)
    (hindex : rowLattice.index = Nat.card B) :
    rowLattice = pointMap.ker := by
  have hker_index : pointMap.ker.index = Nat.card B := by
    rw [AddSubgroup.index_ker]
    simp [AddMonoidHom.range_eq_top.mpr hsurj]
  letI : pointMap.ker.FiniteIndex := ⟨by rw [hker_index]; exact (Nat.card_pos (α := B)).ne'⟩
  apply AddSubgroup.eq_of_index_dvd_index hrows
  rw [hindex, hker_index]

#print axioms X011RelationLattice.equals_relation_kernel_of_index

end X011RelationLattice
