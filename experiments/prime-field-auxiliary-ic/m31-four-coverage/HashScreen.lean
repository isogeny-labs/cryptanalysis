import Std.Tactic.BVDecide
import Mathlib.Tactic

namespace M31FourCoverage.HashScreen

/-- The two required marks may coincide. Any later insertions in the
same word preserve all the marks placed by the original endpoint. -/
theorem retained (old marks later : BitVec 64) :
    ((old ||| marks ||| later) &&& marks) = marks := by
  bv_decide

/-- Testing an abscissa before constructing its full point preserves the
sequence and order of surviving points, including repeated inputs. -/
theorem deferred {A B : Type*} (xs : List A) (complete : A → B)
    (keep : A → Bool) (valid : B → Bool) (key : ∀ a, valid (complete a) = keep a) :
    (xs.filter keep).map complete = (xs.map complete).filter valid := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    cases h : keep x <;> simp [h, key, ih]

end M31FourCoverage.HashScreen
