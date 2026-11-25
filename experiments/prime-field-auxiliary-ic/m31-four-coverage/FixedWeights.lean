import HalfOrbit

namespace M31FixedWeights

open M31FiberRecurrence M31PanelInitializer

theorem weighted {K : Type*} [Field K] (s a b : K) (i : Nat) :
    generated s a b (i+1) =
      generated s 0 1 (i+1)*b - generated s 0 1 i*a := by
  induction i using Nat.twoStepInduction with
  | zero => simp [generated]
  | one => simp [generated]
  | more n h j =>
    change s*generated s a b (n+2) - generated s a b (n+1) =
      (s*generated s 0 1 (n+2) - generated s 0 1 (n+1))*b -
      (s*generated s 0 1 (n+1) - generated s 0 1 n)*a
    rw [j,h]
    change _ = (s*(s*generated s 0 1 (n+1)-generated s 0 1 n) -
      generated s 0 1 (n+1))*b - _
    rw [show generated s 0 1 (n+2) = s*generated s 0 1 (n+1) - generated s 0 1 n by rfl]
    ring

def fixed : M := 1330526061

theorem fixed_half (a b : M) (i : Nat) :
    generated fixed a b (i+64) = -generated fixed a b i := by
  have h := M31HalfOrbit.stride fixed a b 5 i
  have zero : forward^[5] fixed = 0 := by decide +kernel
  rw [zero,zero_mul,zero_sub] at h
  exact h

private def invariant (s a b : M) := a^2 + b^2 + s^2 - a*b*s - 4

private theorem doubled (s a b : M) (h : invariant s a b = 0) :
    invariant (forward s) (forward a) (forward b) = 0 := by
  unfold invariant forward at *
  linear_combination (a^2+b^2+s^2+a*b*s-4)*h

private theorem iter_doubled (s a b : M) (h : invariant s a b = 0) (n : Nat) :
    invariant (forward^[n] s) (forward^[n] a) (forward^[n] b) = 0 := by
  induction n with
  | zero => exact h
  | succ n ih => simpa only [Function.iterate_succ_apply'] using doubled _ _ _ ih

private instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

private theorem neighbors (a b : M) (h : invariant fixed a b = 0) :
    forward^[7] a = forward^[7] b := by
  have h' := iter_doubled _ _ _ h 7
  have endpt : forward^[7] fixed = 2 := by decide +kernel
  rw [endpt] at h'
  unfold invariant at h'
  apply sub_eq_zero.mp
  apply sq_eq_zero_iff.mp
  linear_combination h'

theorem fixed_terminal (a b : M) (h : a^2 + b^2 + fixed^2 - a*b*fixed - 4 = 0) (i : Nat) :
    forward^[7] (generated fixed a b i) = forward^[7] a := by
  have edges (n : Nat) :
      invariant fixed (generated fixed a b n) (generated fixed a b (n+1)) = 0 := by
    induction n with
    | zero => exact h
    | succ n ih =>
      change invariant fixed _ (fixed*generated fixed a b (n+1) - generated fixed a b n) = 0
      unfold invariant at *
      linear_combination ih
  induction i with
  | zero => rfl
  | succ i ih => exact (neighbors _ _ (edges i)).symm.trans ih

def fixedNeighbor (a : M) : M :=
  (a*fixed + squareRoot ((a^2-4)*(fixed^2-4))) * 1073741824

def panel : List Nat := terminals ++ M31HalfOrbit.holdout

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
private theorem seeds_valid : ∀ n ∈ panel,
    invariant fixed (leaf n) (fixedNeighbor (leaf n)) = 0 ∧ forward^[7] (leaf n) = n := by
  decide +kernel

theorem weighted_terminal (t : Nat) (row : t ∈ panel) (i : Nat) :
    forward^[7] (generated fixed 0 1 (i+1) * fixedNeighbor (leaf t) -
      generated fixed 0 1 i * leaf t) = t := by
  obtain ⟨h,ht⟩ := seeds_valid t row
  rw [← weighted]
  exact (fixed_terminal _ _ h _).trans ht

end M31FixedWeights
