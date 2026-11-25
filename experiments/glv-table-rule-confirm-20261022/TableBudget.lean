import Std.Tactic

/-!
The pure arithmetic of the GLV r-multiplier table selector in `src/curve.c`.

Historical scope (theorems up to `loop48_le_loop12`): the C file at commit
`42761f85` (SHA-256 3f3a100d635d814bdfa0f6624a40b9d77c9c564f65db2bbc568dcd4b55285efe)
starts the loop at eight, doubles while `2*r ≤ budget ∧ 2*r ≤ 32`, and uses
`budget = sqrt_nm / (12*lg)` after the held-out rule change. The prior rule
used 48. `loopResult` unrolls the two possible successful doublings;
`loopResult_fixed` proves another step cannot change the result.

Current scope (theorems from `capFor_below40` on): the size-dependent cap of
`src/curve.c` at commit `e71ebeca` (SHA-256
e1d624e58c54f25f9225be97481b50c0ed406cedcfdffa8ba66f01a5fbed7f63). The cap is
`rcap = lg ≥ 40 ? 128 : 32` and the loop is
`while (rr*2 ≤ rbudget && rr*2 ≤ rcap) rr *= 2` from `rr = 8`, still with
`rbudget = sqrt_nm / (12*lg)`. `stepCap`/`loopCap` model four literal
iterations (8 → 16 → 32 → 64 → 128 is the longest chain), and
`loopCap_fixed` proves a fifth cannot change the result for either cap.

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

/-! ### Current selector: size-dependent cap (`src/curve.c` at `e71ebeca`) -/

/-- The cap of the current C selector: 32 below 40 bits (`lg < 40`), 128 from
40 bits up (`lg >= 40 ? 128 : 32`). -/
def capFor (lg : Nat) : Nat := if lg < 40 then 32 else 128

/-- One literal iteration of the current C loop guard and doubling. -/
def stepCap (cap budget r : Nat) : Nat :=
  if r * 2 ≤ budget ∧ r * 2 ≤ cap then r * 2 else r

/-- Four iterations from eight suffice for caps up to 128 (8 → 16 → 32 → 64 → 128). -/
def loopCap (cap budget : Nat) : Nat :=
  stepCap cap budget (stepCap cap budget (stepCap cap budget (stepCap cap budget 8)))

/-- The cap-128 selector as a five-case formula. -/
def tableSize128 (budget : Nat) : Nat :=
  if budget < 16 then 8 else if budget < 32 then 16 else if budget < 64 then 32
  else if budget < 128 then 64 else 128

/-- The current selector as a function of `sqrt_nm` (`s`) and `lg`. -/
def select (s lg : Nat) : Nat := loopCap (capFor lg) (s / (12 * lg))

theorem capFor_below40 (lg : Nat) (h : lg < 40) : capFor lg = 32 := by
  simp [capFor, h]

theorem capFor_from40 (lg : Nat) (h : 40 ≤ lg) : capFor lg = 128 := by
  have : ¬ lg < 40 := by omega
  simp [capFor, this]

theorem loopCap32_eq_tableSize (budget : Nat) :
    loopCap 32 budget = tableSize budget := by
  by_cases h16 : budget < 16
  · have hn16 : ¬ 16 ≤ budget := by omega
    simp [loopCap, stepCap, tableSize, h16, hn16]
  · by_cases h32 : budget < 32
    · have hg16 : 16 ≤ budget := by omega
      have hn32 : ¬ 32 ≤ budget := by omega
      simp [loopCap, stepCap, tableSize, h16, h32, hg16, hn32]
    · have hg16 : 16 ≤ budget := by omega
      have hg32 : 32 ≤ budget := by omega
      simp [loopCap, stepCap, tableSize, h16, h32, hg16, hg32]

theorem loopCap128_eq_tableSize128 (budget : Nat) :
    loopCap 128 budget = tableSize128 budget := by
  by_cases h16 : budget < 16
  · have hn16 : ¬ 16 ≤ budget := by omega
    simp [loopCap, stepCap, tableSize128, h16, hn16]
  · have hg16 : 16 ≤ budget := by omega
    by_cases h32 : budget < 32
    · have hn32 : ¬ 32 ≤ budget := by omega
      simp [loopCap, stepCap, tableSize128, h16, h32, hg16, hn32]
    · have hg32 : 32 ≤ budget := by omega
      by_cases h64 : budget < 64
      · have hn64 : ¬ 64 ≤ budget := by omega
        simp [loopCap, stepCap, tableSize128, h16, h32, h64, hg16, hg32, hn64]
      · have hg64 : 64 ≤ budget := by omega
        by_cases h128 : budget < 128
        · have hn128 : ¬ 128 ≤ budget := by omega
          simp [loopCap, stepCap, tableSize128, h16, h32, h64, h128, hg16, hg32, hg64, hn128]
        · have hg128 : 128 ≤ budget := by omega
          simp [loopCap, stepCap, tableSize128, h16, h32, h64, h128, hg16, hg32, hg64, hg128]

theorem loopCap32_eq_loopResult (budget : Nat) :
    loopCap 32 budget = loopResult budget := by
  rw [loopCap32_eq_tableSize, loopResult_eq_tableSize]

theorem loopCap32_fixed (budget : Nat) :
    stepCap 32 budget (loopCap 32 budget) = loopCap 32 budget := by
  unfold loopCap stepCap
  repeat' split
  all_goals omega

theorem loopCap128_fixed (budget : Nat) :
    stepCap 128 budget (loopCap 128 budget) = loopCap 128 budget := by
  unfold loopCap stepCap
  repeat' split
  all_goals omega

theorem tableSize128_cases (budget : Nat) :
    tableSize128 budget = 8 ∨ tableSize128 budget = 16 ∨ tableSize128 budget = 32 ∨
    tableSize128 budget = 64 ∨ tableSize128 budget = 128 := by
  unfold tableSize128
  repeat' split
  all_goals simp

theorem tableSize128_mono {a b : Nat} (h : a ≤ b) :
    tableSize128 a ≤ tableSize128 b := by
  unfold tableSize128
  repeat' split
  all_goals omega

theorem tableSize_le_tableSize128 (budget : Nat) :
    tableSize budget ≤ tableSize128 budget := by
  unfold tableSize tableSize128
  repeat' split
  all_goals omega

theorem tableSize128_eq_tableSize_below32 (budget : Nat) (h : budget < 64) :
    tableSize128 budget = tableSize budget := by
  unfold tableSize tableSize128
  repeat' split
  all_goals omega

theorem select_below40 (s lg : Nat) (h : lg < 40) :
    select s lg = loopResult (s / (12 * lg)) := by
  rw [select, capFor_below40 lg h, loopCap32_eq_loopResult]

theorem select_from40 (s lg : Nat) (h : 40 ≤ lg) :
    select s lg = tableSize128 (s / (12 * lg)) := by
  rw [select, capFor_from40 lg h, loopCap128_eq_tableSize128]

theorem select_bounds (s lg : Nat) :
    8 ≤ select s lg ∧ select s lg ≤ capFor lg := by
  by_cases h : lg < 40
  · rw [select_below40 s lg h, capFor_below40 lg h]
    exact loopResult_bounds _
  · have h40 : 40 ≤ lg := by omega
    rw [select_from40 s lg h40, capFor_from40 lg h40]
    rcases tableSize128_cases (s / (12 * lg)) with h | h | h | h | h <;> simp [h]

theorem select_cases (s lg : Nat) :
    (lg < 40 → select s lg = 8 ∨ select s lg = 16 ∨ select s lg = 32) ∧
    (40 ≤ lg → select s lg = 8 ∨ select s lg = 16 ∨ select s lg = 32 ∨
      select s lg = 64 ∨ select s lg = 128) := by
  constructor
  · intro h
    rw [select_below40 s lg h, loopResult_eq_tableSize]
    exact tableSize_cases _
  · intro h
    rw [select_from40 s lg h]
    exact tableSize128_cases _

theorem select_mono_budget {s s' : Nat} (lg : Nat) (h : s ≤ s') :
    select s lg ≤ select s' lg := by
  have hb : s / (12 * lg) ≤ s' / (12 * lg) := Nat.div_le_div_right h
  by_cases h40 : lg < 40
  · rw [select_below40 s lg h40, select_below40 s' lg h40,
      loopResult_eq_tableSize, loopResult_eq_tableSize]
    exact tableSize_mono hb
  · have h40' : 40 ≤ lg := by omega
    rw [select_from40 s lg h40', select_from40 s' lg h40']
    exact tableSize128_mono hb

/-- Below 40 bits the current selector is exactly the rule on `main` before
this change (divisor 12, cap 32). -/
theorem select_eq_old_below40 (s lg : Nat) (h : lg < 40) :
    select s lg = loopResult (s / (12 * lg)) :=
  select_below40 s lg h

/-- The current selector never picks a smaller table than the previous
(divisor 12, cap 32) selector for the same `sqrt_nm` and `lg`. -/
theorem old_le_select (s lg : Nat) :
    loopResult (s / (12 * lg)) ≤ select s lg := by
  by_cases h : lg < 40
  · rw [select_below40 s lg h]
    exact Nat.le_refl _
  · have h40 : 40 ≤ lg := by omega
    rw [select_from40 s lg h40, loopResult_eq_tableSize]
    exact tableSize_le_tableSize128 _

/-- Combined with the 48 → 12 divisor theorem: the current selector never picks
a smaller table than the original divisor-48, cap-32 baseline. -/
theorem baseline48_le_select (s lg : Nat) (hlg : 0 < lg) :
    loopResult (s / (48 * lg)) ≤ select s lg :=
  Nat.le_trans (loop48_le_loop12 s lg hlg) (old_le_select s lg)

#print axioms loopResult_eq_tableSize
#print axioms loopResult_fixed
#print axioms tableSize_cases
#print axioms loopResult_bounds
#print axioms tableSize_mono
#print axioms budget48_le_budget12
#print axioms table48_le_table12
#print axioms loop48_le_loop12

#print axioms capFor_below40
#print axioms capFor_from40
#print axioms loopCap32_eq_tableSize
#print axioms loopCap128_eq_tableSize128
#print axioms loopCap32_eq_loopResult
#print axioms loopCap32_fixed
#print axioms loopCap128_fixed
#print axioms tableSize128_cases
#print axioms tableSize128_mono
#print axioms tableSize_le_tableSize128
#print axioms tableSize128_eq_tableSize_below32
#print axioms select_below40
#print axioms select_from40
#print axioms select_bounds
#print axioms select_cases
#print axioms select_mono_budget
#print axioms select_eq_old_below40
#print axioms old_le_select
#print axioms baseline48_le_select

end GlvTableBudget
