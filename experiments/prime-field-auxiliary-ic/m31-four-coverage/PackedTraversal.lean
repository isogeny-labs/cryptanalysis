import PairedCubic

namespace M31PackedTraversal

-- Decompose the flattened lane index exactly as in the paired NEON loop.
def slot (v n : Nat) : Nat :=
  let offset := (n / (4*v)) * (2*v)
  let j := (n % (4*v)) / 4
  let k := n % 4
  offset + (j/(v/2))*64 + (j%(v/2))*4 + k

set_option maxRecDepth 8192 in
theorem all_slots : ∀ v ∈ [4,8,16,32], ((List.range 128).map (slot v)).Perm (List.range 128) := by
  decide +kernel

-- Sorting a subset of accepted points can use these words without collisions.
theorem no_alias {x y u v : Nat} (hy : y < 2147483647) (hv : v < 2147483647)
    (eq : M31PairedCubic.pack x y = M31PairedCubic.pack u v) : (x,y) = (u,v) := by
  obtain ⟨hx,ly⟩ := M31PairedCubic.unpack x y hy
  obtain ⟨hu,lv⟩ := M31PairedCubic.unpack u v hv
  rw [eq] at hx ly
  exact Prod.ext (hx.symm.trans hu) (ly.symm.trans lv)

end M31PackedTraversal
