import TerminalSeparation

namespace M31TerminalLift
open M31TerminalSeparation M31ArchiveRoots M31ArchiveData

-- The benchmark uses (p+1)/4 = 2^29 to obtain its candidate square root.
private def p := 2147483647
def accepts (x : Nat) : Bool :=
  let r := (x^3+2*x+14)%p
  let y := (fun v : Nat => (v*v)%p)^[29] r
  (y*y)%p == r

theorem matches_archive :
    (roots.filter accepts).toFinset = (archived.map Prod.fst).toFinset := by decide +kernel

private def sharedClass := roots.filter (fun x => label 31 x = 2)

theorem witnesses :
    3 ∈ roots ∧ 1533993268 ∈ roots ∧
    label 29 3 = 0 ∧ label 29 1533993268 = 0 ∧
    accepts 3 = true ∧ accepts 1533993268 = false := by decide +kernel

-- Any classifier that sees only the fixed-depth terminal must assign the
-- same answer to every member of this class.
theorem unavoidable_errors (predict : Nat → Bool) :
    7 ≤ (sharedClass.filter (fun x => predict (label 31 x) != accepts x)).length := by
  have eqn : (sharedClass.filter (fun x => predict (label 31 x) != accepts x)) =
      sharedClass.filter (fun x => predict 2 != accepts x) := by
    apply List.filter_congr
    intro x hx
    have ht : label 31 x = 2 := by simpa [sharedClass] using (List.mem_filter.mp hx).2
    rw [ht]
  rw [eqn]
  cases predict 2 <;> decide +kernel
-- A lookup in the archived positive labels outside the shared class
-- attains the bound over all 32 roots.
def best (t : Nat) := t != 2 && (archived.map (fun q => label 31 q.1)).contains t

theorem attained :
    (roots.filter (fun x => best (label 31 x) != accepts x)).length = 7 := by decide +kernel
theorem minimum_errors (predict : Nat → Bool) :
    7 ≤ (roots.filter (fun x => predict (label 31 x) != accepts x)).length := by
  have sub : sharedClass.Sublist roots := List.filter_sublist
  exact (unavoidable_errors predict).trans ((sub.filter _).length_le)

end M31TerminalLift
