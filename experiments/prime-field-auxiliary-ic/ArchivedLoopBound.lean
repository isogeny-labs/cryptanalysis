import Std

namespace M31ArchivedLoopBound

/-! All durations are in nanoseconds. For the three November 15 retrospective
v2-batch records, round cold wall down and matched rho up to integer ns.
Allow 50,000 ns in either direction around each printed loop time. These are
display-rounding allowances, not confidence limits for repeated runs.

The model holds the non-loop portion of the observed cold wall fixed. The
new loop may take any nonnegative integer duration. Its duration multiplied
by the proposed speedup ceiling must cover the original loop duration. -/

structure Observation where
  coldLower : Nat
  loopLower : Nat
  loopUpper : Nat
  rhoUpper : Nat

def seed0 : Observation := ⟨9685107568, 9676460000, 9676560000, 7091596⟩
def seed1 : Observation := ⟨5167235504, 5160030000, 5160130000, 21868217⟩
def seed2 : Observation := ⟨11667566436, 11662550000, 11662650000, 18318453⟩

def fits (r : Observation) (oldLoop rest newLoop : Nat) : Prop :=
  r.coldLower ≤ rest + oldLoop ∧ r.loopLower ≤ oldLoop ∧
  oldLoop ≤ r.loopUpper ∧ rest + newLoop ≤ r.rhoUpper

theorem zeroLoopInsufficient (oldLoop rest newLoop : Nat) :
    ¬ fits seed0 oldLoop rest newLoop := by
  simp only [fits, seed0]
  omega

theorem seed1RequiresMore (oldLoop rest newLoop : Nat)
    (h : fits seed1 oldLoop rest newLoop) : 349 * newLoop < oldLoop := by
  simp only [fits, seed1] at h
  omega

theorem seed2RequiresMore (oldLoop rest newLoop : Nat)
    (h : fits seed2 oldLoop rest newLoop) : 870 * newLoop < oldLoop := by
  simp only [fits, seed2] at h
  omega

end M31ArchivedLoopBound
