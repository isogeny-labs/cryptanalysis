import MaskEmit
import Init.Data.List.Perm

namespace M31BufferBound
open M31MaskEmit

theorem lanes_bound (m : Word) : (emit m).length ≤ 64 := by
  obtain ⟨mem,ordered⟩ := emit_spec m
  have nd : (emit m).Nodup := ordered.imp (fun {a b} hab eq => by
    subst b
    exact (BitVec.lt_irrefl a) hab)
  let lanes := (List.range 64).map (BitVec.ofNat 64)
  have subset : emit m ⊆ lanes := by
    intro i hi
    have hp := (mem i).mp hi
    unfold present at hp
    have small : i < 64#64 := by bv_decide
    apply List.mem_map.mpr
    exact ⟨i.toNat, List.mem_range.mpr small, by simp⟩
  simpa [lanes] using nd.length_le_of_subset subset

theorem buffer_bound (lo hi : Word) :
    (emit lo ++ emit hi.reverse).length ≤ 128 := by
  have a := lanes_bound lo
  have b := lanes_bound hi.reverse
  rw [List.length_append]
  omega

end M31BufferBound
