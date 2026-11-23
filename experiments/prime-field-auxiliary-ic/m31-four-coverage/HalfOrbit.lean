import FiberOrbit
import PanelInitializer

namespace M31HalfOrbit

open M31FiberRecurrence M31PanelInitializer

/-- A recurrence on positions spaced by h yields one on positions spaced by 2h. -/
theorem double_stride {K : Type*} [Field K] (x : Nat → K) (s : K) (h : Nat)
    (rec : ∀ i, x (i+2*h) = s*x (i+h) - x i) (i : Nat) :
    x (i+4*h) = (s*s-2)*x (i+2*h) - x i := by
  have r₀ := rec i
  have r₁ := rec (i+h)
  have r₂ := rec (i+2*h)
  rw [show i+h+2*h = i+3*h by omega, show i+h+h = i+2*h by omega] at r₁
  rw [show i+2*h+2*h = i+4*h by omega, show i+2*h+h = i+3*h by omega] at r₂
  linear_combination r₂ + s*r₁ + r₀

theorem stride (s a b : M) (n i : Nat) :
    generated s a b (i+2*2^n) =
    forward^[n] s * generated s a b (i+2^n) - generated s a b i := by
  induction n generalizing i with
  | zero => rfl
  | succ n ih =>
    have h := double_stride (generated s a b) (forward^[n] s) (2^n) ih i
    rw [pow_succ 2 n, Function.iterate_succ_apply', forward,
        show 2*(2^n*2) = 4*2^n by omega, show 2^n*2 = 2*2^n by omega]
    exact h

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
private theorem panel_step : ∀ t ∈ terminals, forward^[5] (step (t : M)) = 0 := by decide +kernel

theorem half_period (t : Nat) (row : t ∈ terminals) (a b : M) (i : Nat) :
    generated (step t) a b (i+64) = -generated (step t) a b i := by
  have h := stride (step t) a b 5 i
  rw [panel_step t row, zero_mul, zero_sub] at h
  exact h

def holdout : List Nat :=
  [1796175156, 1097735216, 1207169086, 1677359050,
   1364480087, 1003968985, 261962938, 1027955804,
   1942960888, 1222201813, 1494546936, 1356452812,
   1616953319, 540037420, 1052133300, 1689239265,
   1873106881, 1135546232, 1867602217, 204899042,
   786025114, 655763265, 378491209, 1888850491,
   517818874, 905453929, 668130631, 1942559302,
   652479193, 2089701164, 1165125955, 1436984184]

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
theorem holdout_distinct : holdout.Nodup ∧ ∀ t ∈ holdout, t ∉ terminals := by decide +kernel

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
private theorem holdout_step : ∀ t ∈ holdout, forward^[5] (step (t : M)) = 0 := by decide +kernel

theorem holdout_half_period (t : Nat) (row : t ∈ holdout) (a b : M) (i : Nat) :
    generated (step t) a b (i+64) = -generated (step t) a b i := by
  have h := stride (step t) a b 5 i
  rw [holdout_step t row, zero_mul, zero_sub] at h
  exact h

end M31HalfOrbit
