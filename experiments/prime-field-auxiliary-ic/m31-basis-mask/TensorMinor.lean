import Mathlib.LinearAlgebra.Matrix.Rank
import Mathlib.Data.ZMod.Basic
import Mathlib.Data.List.Nodup
import Projection

namespace M31Projection.Tensor

abbrev W := BitVec 31

set_option maxRecDepth 50000 in
set_option maxHeartbeats 8000000 in
theorem complement_distinct : (coordinates.map (fun x => x &&& ~~~mask)).Nodup := by
  decide +kernel

def splice (a b : W) := (a &&& mask) ||| (b &&& ~~~mask)

theorem splice_member (a b : W) (ha : a ∈ coordinates) (hb : b ∈ coordinates) :
    splice a b ∈ coordinates ↔ a = b := by
  constructor
  · intro h
    have left : splice a b &&& mask = a &&& mask := by unfold splice; bv_decide
    have right : splice a b &&& ~~~mask = b &&& ~~~mask := by unfold splice; bv_decide
    exact (List.inj_on_of_nodup_map frozen_labels_distinct h ha left).symm.trans
      (List.inj_on_of_nodup_map complement_distinct h hb right)
  · rintro rfl
    have e : splice a a = a := by unfold splice; bv_decide
    simpa only [e] using ha

abbrev Index := Fin coordinates.length

def minor : Matrix Index Index (ZMod 2) :=
  fun i j => if splice (coordinates.get i) (coordinates.get j) ∈ coordinates then 1 else 0

theorem minor_identity : minor = 1 := by
  ext i j
  have h := splice_member _ _ (List.get_mem coordinates i) (List.get_mem coordinates j)
  have nd := List.Nodup.of_map _ frozen_labels_distinct
  simp only [minor, Matrix.one_apply, h, nd.get_inj_iff]

theorem minor_rank : minor.rank = 195 := by
  rw [minor_identity, Matrix.rank_one, Fintype.card_fin]
  decide +kernel

end M31Projection.Tensor
