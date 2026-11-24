import Mathlib.Tactic

namespace M31GroupedLabels

variable {P L : Type}

/-- Pair each compacted scratch value with the original offset kept in ids. -/
def collect (prepare : Nat → Option P) (ids : List Nat) : List (Nat × P) :=
  ids.filterMap (fun i => (prepare i).map (fun v => (i,v)))

/-- The scatter loop consumes compacted entries in increasing scratch-slot order. -/
def scatter (label : P → L) (base : Nat) (out : Nat → L) : List (Nat × P) → Nat → L
  | [] => out
  | (i,v)::rest => scatter label base (Function.update out (base+i) (label v)) rest

/-- The scratch count fits the allocated number of visited lanes, at every prefix. -/
theorem capacity (prepare : Nat → Option P) (ids : List Nat) :
    (collect prepare ids).length ≤ ids.length := List.length_filterMap_le ..

/-- All addresses, including addresses outside the group and rejected inputs,
have precisely the value given by a direct write at the original input position. -/
theorem scatter_spec (prepare : Nat → Option P) (label : P → L) (base : Nat)
    (ids : List Nat) (out : Nat → L) (addr : Nat) :
    scatter label base out (collect prepare ids) addr =
      if base ≤ addr ∧ addr-base ∈ ids then
        ((prepare (addr-base)).map label).getD (out addr)
      else out addr := by
  induction ids generalizing out with
  | nil => simp [collect, scatter]
  | cons i rest ih =>
    unfold collect at ih
    by_cases atSlot : addr = base+i
    · subst addr
      cases h : prepare i with
      | none => simp [collect, h, ih]
      | some v => simp [collect, h, scatter, ih, Function.update]
    · have guard : base ≤ addr → addr-base ≠ i := by omega
      cases h : prepare i with
      | none =>
        simp only [collect, List.filterMap_cons, h, Option.map_none]
        rw [ih]
        by_cases low : base ≤ addr <;> simp [low, guard]
      | some v =>
        simp only [collect, List.filterMap_cons, h, Option.map_some, scatter]
        rw [ih, Function.update_of_ne atSlot]
        by_cases low : base ≤ addr <;> simp [low, guard]

/-- Contiguous groups use absolute offsets within the block. Group boundaries
may change without changing any result at a visited lane. -/
theorem group_lane (prepare : Nat → Option P) (label : P → L) (base first width b : Nat)
    (k : Fin 4) (lo : first ≤ b) (hi : b < first + width) (out : Nat → L) :
    scatter label base out (collect prepare (List.range' (4*first) (4*width)))
        (base + (4*b+k.val)) =
      ((prepare (4*b+k.val)).map label).getD (out (base + (4*b+k.val))) := by
  have hk := k.isLt
  have mem : 4*b+k.val ∈ List.range' (4*first) (4*width) := by
    rw [List.mem_range'_1]
    omega
  simp [scatter_spec, mem]

end M31GroupedLabels
