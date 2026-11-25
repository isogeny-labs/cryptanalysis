import Mathlib.Tactic
import Std.Tactic.BVDecide

namespace M31CoordinateCache

def entry (x : BitVec 32) (b : Bool) := x ||| (if b then 0x80000000 else 0)

theorem encoding (x : BitVec 32) (b : Bool) (canonical : x < 0x7fffffff) :
    entry x b &&& 0x7fffffff = x ∧ entry x b ≠ 0x7fffffff ∧
    ((entry x b).getLsbD 31 = b) := by
  unfold entry
  cases b <;> bv_decide

/-- Linear probing enumerates every slot exactly once before wrapping. -/
theorem probe_permutation (start i j : Nat) (hi : i < 131072) (hj : j < 131072) :
    (start+i)%131072 = (start+j)%131072 ↔ i=j := by omega

/-- A fully checked batch of hits may reuse its bits. Any miss recomputes the batch. -/
theorem batch_result (label : Nat → Bool) (cached : Nat → Option Bool)
    (sound : ∀ x b, cached x = some b → b = label x) (xs : List Nat) :
    ((xs.mapM cached).getD (xs.map label)) = xs.map label := by
  have exactHit : ∀ (ys : List Nat) (bs : List Bool),
      ys.mapM cached = some bs → bs = ys.map label := by
    intro ys
    induction ys with
    | nil => simp
    | cons x rest ih =>
      intro bs h
      cases hx : cached x with
      | none => simp [List.mapM_cons, hx] at h
      | some b =>
        cases ht : rest.mapM cached with
        | none => simp [List.mapM_cons, hx, ht] at h
        | some tail =>
          simpa [List.mapM_cons, hx, ht, sound x b hx, ih tail ht] using h.symm
  cases h : xs.mapM cached with
  | none => rfl
  | some bs => exact exactHit xs bs h

/-- Each miss carries its destination; classification returns the corresponding lane label. -/
def scatter (label initial : Nat → Bool) : List Nat → Nat → Bool
  | [] => initial
  | i :: rest => scatter label (Function.update initial i (label i)) rest

theorem scatter_spec (label initial : Nat → Bool) (indices : List Nat) (j : Nat) :
    scatter label initial indices j = if j ∈ indices then label j else initial j := by
  induction indices generalizing initial with
  | nil => simp [scatter]
  | cons i rest ih =>
    rw [scatter, ih]
    by_cases h : j ∈ rest <;> by_cases e : j = i <;> simp [h, e]

theorem compact_result (label initial : Nat → Bool) (misses : List Nat)
    (hits : ∀ j, j ∉ misses → initial j = label j) :
    scatter label initial misses = label := by
  funext j
  rw [scatter_spec]
  split <;> simp_all

end M31CoordinateCache
