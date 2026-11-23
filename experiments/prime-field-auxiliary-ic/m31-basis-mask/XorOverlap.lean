import Mathlib.Tactic
import Projection

namespace M31Projection.Overlap

abbrev W := BitVec 31

/-- The map is a witness. Its construction need not be trusted as a uniqueness test:
the certificate verifies its answer separately for each increasing pair. -/
private def pairs := coordinates.flatMap fun a =>
  (coordinates.filter (fun b => a < b)).map fun b => (a,b)

private def witness : Std.HashMap W (W × W) :=
  pairs.foldl (fun t ab => t.insert (ab.1 ^^^ ab.2) ab) {}

private theorem checked :
    coordinates.all (fun a => coordinates.all (fun b =>
      decide (a < b) == false || witness[a ^^^ b]? == some (a,b))) = true := by
  native_decide

private theorem decode {a b : W} (ha : a ∈ coordinates) (hb : b ∈ coordinates)
    (hlt : a < b) : witness[a ^^^ b]? = some (a,b) := by
  have h := List.all_eq_true.mp (List.all_eq_true.mp checked a ha) b hb
  simpa [hlt] using h

private def ordered (x y : W) := if x < y then (x,y) else (y,x)

private theorem translate_decode (x d : W) (hd : d ≠ 0)
    (hx : x ∈ coordinates) (hy : x ^^^ d ∈ coordinates) :
    witness[d]? = some (ordered x (x ^^^ d)) := by
  unfold ordered
  split
  next h =>
    have e := decode hx hy h
    rwa [show x ^^^ (x ^^^ d) = d by bv_decide] at e
  next h =>
    have e := decode hy hx (show x ^^^ d < x by bv_decide)
    rwa [show (x ^^^ d) ^^^ x = d by bv_decide] at e

/-- For any nonzero translation, fixing one point of the overlap leaves
only that point and its translated partner as possible overlap points. -/
theorem only_partners (x y d : W) (hd : d ≠ 0)
    (hx : x ∈ coordinates) (hxd : x ^^^ d ∈ coordinates)
    (hy : y ∈ coordinates) (hyd : y ^^^ d ∈ coordinates) :
    y = x ∨ y = x ^^^ d := by
  have h := Option.some.inj ((translate_decode x d hd hx hxd).symm.trans
    (translate_decode y d hd hy hyd))
  unfold ordered at h
  split at h <;> split at h <;> simp only [Prod.mk.injEq] at h <;> grind

end M31Projection.Overlap
