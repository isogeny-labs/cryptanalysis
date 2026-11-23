import Mathlib

namespace M31LiftHistory

private def parse (line : String) : Option (ℕ × ℕ × ℕ) := do
  let [h,b,n] := line.splitOn "," | none
  return (← h.toNat?, ← b.toNat?, ← n.toNat?)

private def data := (((include_str "history12.csv").trimAscii.toString.splitOn "\n").drop 1).toArray
private def entry (i : ℕ) := parse (data[i]?.getD "")
def count (h : Fin 4096) (b : Bool) : ℕ :=
  ((entry (2*h.val + b.toNat)).getD (0,0,0)).2.2

theorem completeTable : data.size = 8192 ∧
    ∀ i : Fin 8192, (entry i.val).any
      (fun row => row.1 == i.val/2 && row.2.1 == i.val%2 && row.2.2 ≥ 260209) := by
  native_decide

def score (f : Fin 4096 → Bool) := ∑ h, count h (f h)

theorem noPureHistory (h : Fin 4096) (b : Bool) : count h b ≥ 260209 := by
  have : ∀ x : Fin 4096, ∀ y : Bool, count x y ≥ 260209 := by native_decide
  exact this h b

private theorem bestBinaryScore {H : Type*} [Fintype H] (c : H → Bool → ℕ) :
    IsGreatest (Set.range (fun f : H → Bool => ∑ h, c h (f h)))
      (∑ h, max (c h false) (c h true)) := by
  constructor
  · refine ⟨fun h => decide (c h false ≤ c h true), ?_⟩
    apply Finset.sum_congr rfl
    intro h _
    by_cases le : c h false ≤ c h true
    · simp [le]
    · simp [le, max_eq_left (le_of_not_ge le)]
  · rintro _ ⟨f,rfl⟩
    apply Finset.sum_le_sum
    intro h _
    cases f h <;> simp

theorem bestScore : IsGreatest (Set.range score) 1074925959 := by
  have total : (∑ h, max (count h false) (count h true)) = 1074925959 := by native_decide
  exact total ▸ bestBinaryScore count

theorem totalCount : (∑ h : Fin 4096, (count h false + count h true)) = 2147483647 := by native_decide

/-- A batch of coordinatewise squarings preserves each lane's exponent. -/
theorem batchPower {R I : Type*} [Monoid R] (input : I → R) (k : ℕ) (j : I) :
    (((fun v : I → R => fun i => v i * v i)^[k]) input) j = (input j)^(2^k) := by
  induction k with
  | zero => simp
  | succ k ih =>
    rw [Function.iterate_succ_apply', pow_succ (2 : ℕ), pow_mul, pow_two]
    exact congrArg₂ (· * ·) ih ih

/-- Rotating a coordinate once and its square twice preserves the
eligibility input at every position of the orbit. -/
theorem orbitSquare (x : ZMod 2147483647) (j : ℕ) :
    ((fun u => 2*(2*u))^[j]) (x^2) = (((fun u => 2*u)^[j]) x)^2 := by
  induction j with
  | zero => rfl
  | succ j ih =>
    simp only [Function.iterate_succ_apply', ih]
    ring

namespace Smooth47

private def rows := (((include_str "smooth_history.csv").trimAscii.toString.splitOn "\n").drop 1).toArray
private def cell (i : ℕ) := parse (rows[i]?.getD "")
def n (h : Fin 1024) (b : Bool) := ((cell (2*h.val+b.toNat)).getD (0,0,0)).2.2

theorem table : rows.size = 2048 ∧ ∀ i : Fin 2048, (cell i.val).any
    (fun r => r.1 == i.val/2 && r.2.1 == i.val%2 && r.2.2 ≥ 778) := by native_decide

set_option autoImplicit false in
theorem population : (∑ h : Fin 1024, n h true) = 925398 ∧
    (∑ h : Fin 1024, (n h false + n h true)) = 1852867 := by native_decide

theorem optimum : IsGreatest (Set.range (fun f : Fin 1024 → Bool => ∑ h, n h (f h)))
    943323 := by
  have total : (∑ h, max (n h false) (n h true)) = 943323 := by native_decide
  exact total ▸ bestBinaryScore n

end Smooth47
end M31LiftHistory
