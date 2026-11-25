import ArchiveData
import ArchiveRoots
import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic.NormNum

namespace M31ArchiveLiftSelection

abbrev F := ZMod 2147483647

def rhs (x : Nat) : F :=
  let t : F := x
  t^3 + 2*t + 14

def ladder (x : F) : Nat → F
  | 0 => 1
  | n+1 => let y := ladder x n; y*y*x

theorem ladder_spec (x : F) (n : Nat) : ladder x n * x = x ^ (2^n) := by
  induction n with
  | zero => simp [ladder]
  | succ n ih =>
    rw [pow_succ 2, pow_mul, ← ih]
    simp only [ladder, pow_two]
    ac_rfl

-- Euler's test on every public input of the archived depth-five fixture.
theorem selected_abscissae :
    (M31ArchiveRoots.roots.filter (fun x => decide (ladder (rhs x) 30 = 1))).mergeSort =
      (M31ArchiveData.archived.map Prod.fst).mergeSort := by native_decide

theorem rejected_count :
    (M31ArchiveRoots.roots.filter (fun x => decide (ladder (rhs x) 30 = -1))).length = 15 := by
  native_decide

end M31ArchiveLiftSelection
