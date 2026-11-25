import Projection

namespace M31Projection.Reciprocal

private def labels := coordinates.map BitVec.toNat

set_option maxRecDepth 50000 in
set_option maxHeartbeats 12000000 in
private theorem checked : labels.all (fun x => labels.all (fun y =>
    decide (x*y % 2147483647 ≠ 1))) = true := by decide +kernel

/-- The archived accepted coordinates contain no reciprocal pair, including a fixed point. -/
theorem no_reciprocal {a b : BitVec 31} (ha : a ∈ coordinates) (hb : b ∈ coordinates) :
    a.toNat * b.toNat % 2147483647 ≠ 1 := by
  have h := List.all_eq_true.mp checked a.toNat (List.mem_map_of_mem ha)
  simpa using List.all_eq_true.mp h b.toNat (List.mem_map_of_mem hb)

end M31Projection.Reciprocal
