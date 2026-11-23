import Mathlib.Tactic

namespace TripleCancellation

variable {G : Type*} [AddCommGroup G]

def triple (p r : G) : Multiset G := r ::ₘ p ::ₘ (-p) ::ₘ 0

theorem remainder (p r : G) : (triple p r).sum = r := by simp [triple]

/-- The leftover point and unordered inverse pair are uniquely determined. -/
theorem identify {p q r s : G} (h : triple p r = triple q s) :
    r = s ∧ (p = q ∨ p = -q) := by
  have hr : r = s := by simpa [remainder] using congrArg Multiset.sum h
  subst s
  have hp : (p ::ₘ (-p) ::ₘ (0 : Multiset G)) = q ::ₘ (-q) ::ₘ 0 := by
    simpa [triple] using h
  have hm : p ∈ q ::ₘ (-q) ::ₘ (0 : Multiset G) := hp ▸ Multiset.mem_cons_self _ _
  exact ⟨rfl, by simpa using hm⟩

end TripleCancellation
