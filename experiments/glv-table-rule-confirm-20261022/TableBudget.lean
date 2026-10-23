import Std.Tactic

/-!
The pure arithmetic of the GLV r-multiplier table selector in `src/curve.c`
(SHA-256 3f3a100d635d814bdfa0f6624a40b9d77c9c564f65db2bbc568dcd4b55285efe).
The C loop starts at eight, doubles while `2*r ≤ budget ∧ 2*r ≤ 32`, and
uses `budget = sqrt_nm / (12*lg)` after the held-out rule change. The prior
rule used 48. `loopResult` unrolls the two possible successful doublings;
`loopResult_fixed` proves another step cannot change the result.

These theorems concern selector arithmetic only. They do not prove C memory
safety, discrete-log correctness, or an operation-count improvement.
-/
namespace GlvTableBudget

/-- The selector as a three-case formula. -/
def tableSize (budget : Nat) : Nat :=
  if budget < 16 then 8 else if budget < 32 then 16 else 32

/-- One literal iteration of the C loop guard and doubling. -/
def step (budget r : Nat) : Nat :=
  if r * 2 ≤ budget ∧ r * 2 ≤ 32 then r * 2 else r

/-- Two iterations from eight suffice because the cap is 32. -/
def loopResult (budget : Nat) : Nat := step budget (step budget 8)

theorem loopResult_eq_tableSize (budget : Nat) :
    loopResult budget = tableSize budget := by
  by_cases h16 : budget < 16
  · have hn16 : ¬ 16 ≤ budget := by omega
    simp [loopResult, step, tableSize, h16, hn16]
  · by_cases h32 : budget < 32
    · have hg16 : 16 ≤ budget := by omega
      have hn32 : ¬ 32 ≤ budget := by omega
      simp [loopResult, step, tableSize, h16, h32, hg16, hn32]
    · have hg16 : 16 ≤ budget := by omega
      have hg32 : 32 ≤ budget := by omega
      simp [loopResult, step, tableSize, h16, h32, hg16, hg32]

theorem loopResult_fixed (budget : Nat) :
    step budget (loopResult budget) = loopResult budget := by
  rw [loopResult_eq_tableSize]
  by_cases h16 : budget < 16
  · simp [tableSize, step, h16]
  · by_cases h32 : budget < 32
    · simp [tableSize, step, h16, h32]
    · simp [tableSize, step, h16, h32]

theorem tableSize_cases (budget : Nat) :
    tableSize budget = 8 ∨ tableSize budget = 16 ∨ tableSize budget = 32 := by
  by_cases h16 : budget < 16
  · simp [tableSize, h16]
  · by_cases h32 : budget < 32
    · simp [tableSize, h16, h32]
    · simp [tableSize, h16, h32]

theorem loopResult_bounds (budget : Nat) :
    8 ≤ loopResult budget ∧ loopResult budget ≤ 32 := by
  rw [loopResult_eq_tableSize]
  rcases tableSize_cases budget with h | h | h <;> simp [h]

theorem tableSize_mono {a b : Nat} (h : a ≤ b) :
    tableSize a ≤ tableSize b := by
  by_cases ha16 : a < 16
  · by_cases hb16 : b < 16
    · simp [tableSize, ha16, hb16]
    · by_cases hb32 : b < 32
      · simp [tableSize, ha16, hb16, hb32]
      · simp [tableSize, ha16, hb16, hb32]
  · have hb16 : ¬ b < 16 := by omega
    by_cases ha32 : a < 32
    · by_cases hb32 : b < 32
      · simp [tableSize, ha16, hb16, ha32, hb32]
      · simp [tableSize, ha16, hb16, ha32, hb32]
    · have hb32 : ¬ b < 32 := by omega
      simp [tableSize, ha16, hb16, ha32, hb32]

theorem budget48_le_budget12 (s lg : Nat) (hlg : 0 < lg) :
    s / (48 * lg) ≤ s / (12 * lg) := by
  apply Nat.div_le_div_left
  · omega
  · omega

theorem table48_le_table12 (s lg : Nat) (hlg : 0 < lg) :
    tableSize (s / (48 * lg)) ≤ tableSize (s / (12 * lg)) :=
  tableSize_mono (budget48_le_budget12 s lg hlg)

theorem loop48_le_loop12 (s lg : Nat) (hlg : 0 < lg) :
    loopResult (s / (48 * lg)) ≤ loopResult (s / (12 * lg)) := by
  rw [loopResult_eq_tableSize, loopResult_eq_tableSize]
  exact table48_le_table12 s lg hlg

#print axioms loopResult_eq_tableSize
#print axioms loopResult_fixed
#print axioms loopResult_bounds
#print axioms tableSize_mono
#print axioms budget48_le_budget12
#print axioms loop48_le_loop12

end GlvTableBudget
