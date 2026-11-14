import Std.Tactic

/-! An exact integer obstruction for the actual q223 source. Actual finite
field elliptic groups, Hasse's theorem, inclusion of rational points and
isogeny invariance of point counts are NOT defined here. The last theorem
states the conditional integer implication faithfully. No custom axioms or
native_decide are used. -/
set_option autoImplicit false
set_option maxRecDepth 10000
set_option maxHeartbeats 2000000
namespace NoBaseFieldCurve223

theorem hasse_radius_integer_bounds :
    (29 : Nat)^2 ≤ 4*223 ∧ 4*223 < (30 : Nat)^2 := by decide

theorem all_hasse_candidates_fail_divisibility :
    ∀ k : Fin 59, ¬ (195+k.val) ∣ (11092292 : Nat) := by decide

theorem no_hasse_count_divides_extension_count
    (m : Nat) (lower : 195 ≤ m) (upper : m ≤ 253) :
    ¬ m ∣ (11092292 : Nat) := by
  have index_bound : m-195 < 59 := by omega
  have identity : 195+(m-195)=m := by omega
  have result := all_hasse_candidates_fail_divisibility ⟨m-195,index_bound⟩
  simpa only [identity] using result

end NoBaseFieldCurve223
