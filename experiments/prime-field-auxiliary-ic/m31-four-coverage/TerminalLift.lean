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

private theorem first_mixed_pair :
    1900319349 ∈ roots ∧ 2008905047 ∈ roots ∧
    label 25 1900319349 = label 25 2008905047 ∧
    accepts 1900319349 = true ∧ accepts 2008905047 = false := by decide +kernel

-- This is an existence criterion for a classifier on this fixture.
-- The positive-label lookup in the backward direction presupposes its labels.
theorem exact_depth (d : Nat) :
    (∃ f : Nat → Bool, ∀ x ∈ roots, f (label d x) = accepts x) ↔ d ≤ 24 := by
  constructor
  · rintro ⟨f, hf⟩
    by_contra late
    obtain ⟨ha,hb,eq25,yes,no⟩ := first_mixed_pair
    have eqd := congrArg (step^[d-25]) eq25
    unfold label at eqd
    rw [← Function.iterate_add_apply, ← Function.iterate_add_apply,
        show d-25+25 = d by omega] at eqd
    have both := congrArg f eqd
    change f (label d _) = f (label d _) at both
    rw [hf _ ha, hf _ hb, yes, no] at both
    contradiction
  · intro early
    classical
    refine ⟨fun t => decide (∃ y ∈ roots, label d y = t ∧ accepts y = true), ?_⟩
    intro x hx
    by_cases yes : accepts x = true
    · simpa only [yes, decide_eq_true_eq] using
        (show ∃ y ∈ roots, label d y = label d x ∧ accepts y = true from ⟨x,hx,rfl,yes⟩)
    · have h : ¬ ∃ y ∈ roots, label d y = label d x ∧ accepts y = true := by
        rintro ⟨y,hy,eq,hit⟩
        exact yes (unique_terminal hy hx early eq ▸ hit)
      simp [h, Bool.eq_false_iff.mpr yes]

end M31TerminalLift
