import Mathlib.Tactic

namespace M31ArchivedRates

/-- Allowed uncertainty of one millisecond on either archived loop duration.
The tested query counts stay fixed. -/
def scenario (control batch qc qb : ℚ) : Prop :=
  (|control-14.412| ≤ 0.001 ∧ |batch-9.67651| ≤ 0.001 ∧ qc=36262094 ∧ qb=34771537) ∨
  (|control-22.2868| ≤ 0.001 ∧ |batch-5.16008| ≤ 0.001 ∧ qc=60080847 ∧ qb=19300166) ∨
  (|control-15.0759| ≤ 0.001 ∧ |batch-11.6626| ≤ 0.001 ∧ qc=41844181 ∧ qb=45496514)

theorem rate_band (control batch qc qb : ℚ) (h : scenario control batch qc qb) :
    1.38 < (control/qc)/(batch/qb) ∧ (control/qc)/(batch/qb) < 1.43 := by
  rcases h with ⟨hc,hb,rfl,rfl⟩ | ⟨hc,hb,rfl,rfl⟩ | ⟨hc,hb,rfl,rfl⟩ <;>
    rw [abs_le] at hc hb <;>
    have hpos : 0 < batch := by linarith [hb.1]
  all_goals
    constructor <;> first
      | apply (lt_div_iff₀ (by positivity)).mpr; linarith [hc.1,hc.2,hb.1,hb.2]
      | apply (div_lt_iff₀ (by positivity)).mpr; linarith [hc.1,hc.2,hb.1,hb.2]

end M31ArchivedRates
