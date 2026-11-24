import XorCompress
import NineExcess
import SixBitQuotient

namespace M31SixBitAddress

private theorem pair_mem (xs : List (BitVec 7)) {x y : BitVec 7}
    (hx : x ∈ xs) (hy : y ∈ xs) (ne : x ≠ y) : x ^^^ y ∈ M31NineExcess.diffs xs := by
  induction xs with
  | nil => simp at hx
  | cons a xs ih =>
    simp only [List.mem_cons] at hx hy
    rcases hx with rfl | hx
    · rcases hy with rfl | hy
      · exact False.elim (ne rfl)
      · exact List.mem_append_left _ (List.mem_map.mpr ⟨y,hy,rfl⟩)
    · rcases hy with rfl | hy
      · exact List.mem_append_left _ (List.mem_map.mpr ⟨x,hx,BitVec.xor_comm _ _⟩)
      · exact List.mem_append_right _ (ih hx hy)

theorem universal (keys : Fin 17 → BitVec 31) :
    ∃ f : BitVec 31 → BitVec 6,
      (∀ a b, f (a ^^^ b) = f a ^^^ f b) ∧
      ∀ i j, f (keys i) = f (keys j) → keys i = keys j := by
  obtain ⟨m,sep⟩ := M31XorCompress.fixed_low_separates keys
  let h := M31XorCompress.hash 24 m
  let xs := List.ofFn (fun i => h (keys i))
  obtain ⟨d,nz,missing⟩ := M31NineExcess.missing_direction xs (by simp [xs])
  refine ⟨fun x => M31SixBitQuotient.quotient d (h x),?_,?_⟩
  · intro a b
    exact (congrArg (M31SixBitQuotient.quotient d) (M31XorCompress.hash_linear 24 m a b)).trans
      (M31SixBitQuotient.linear d (h a) (h b))
  · intro i j eq
    apply sep i j
    rcases (M31SixBitQuotient.equal_iff d _ _ nz).mp eq with same | bad
    · exact same
    · by_contra ne
      exact missing (bad ▸ pair_mem xs (List.mem_ofFn.mpr ⟨i,rfl⟩) (List.mem_ofFn.mpr ⟨j,rfl⟩) ne)

end M31SixBitAddress
