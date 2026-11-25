import Mathlib.Tactic

namespace BackwardFill

variable {α : Type} (key : α → Nat)

/-- Cursor for each bucket equals its start plus its remaining input count. -/
def cursor (start : Nat → Nat) (xs : List α) (b : Nat) :=
  start b + (xs.filter (fun x => key x == b)).length

def dec (c : Nat → Nat) (k : Nat) (b : Nat) := if b = k then c b - 1 else c b

theorem step (start : Nat → Nat) (x : α) (xs : List α) :
    dec (cursor key start (x::xs)) (key x) = cursor key start xs := by
  funext b
  by_cases h : key x = b
  · subst b
    simp [dec, cursor]
  · simp [dec, cursor, h, Ne.symm h]

def finish (c : Nat → Nat) : List α → Nat → Nat
  | [] => c
  | x::xs => finish (dec c (key x)) xs

theorem final_cursor (start : Nat → Nat) (xs : List α) :
    finish key (cursor key start xs) xs = start := by
  induction xs with
  | nil => funext b; simp [finish, cursor]
  | cons x xs ih => simpa [finish, step] using ih

/-- Each pair records the destination and the full key written there. -/
def writes (c : Nat → Nat) : List α → List (Nat × α)
  | [] => []
  | x::xs => let next := dec c (key x)
             (next (key x),x) :: writes next xs

def slots (lo : Nat) : List α → List (Nat × α)
  | [] => []
  | x::xs => (lo+xs.length,x)::slots lo xs

theorem bucket_writes (start : Nat → Nat) (xs : List α) (b : Nat) :
    (writes key (cursor key start xs) xs).filter (fun w => key w.2 == b) =
      slots (start b) (xs.filter (fun x => key x == b)) := by
  induction xs with
  | nil => simp [writes, slots]
  | cons x xs ih =>
    simp only [writes, step]
    by_cases h : key x = b
    · simp [h, ih, slots, cursor]
    · simp [h, ih]

theorem slot_bound (lo : Nat) (xs : List α) (w : Nat × α) (hw : w ∈ slots lo xs) :
    lo ≤ w.1 ∧ w.1 < lo+xs.length := by
  induction xs with
  | nil => simp [slots] at hw
  | cons x xs ih =>
    rcases List.mem_cons.mp hw with rfl | h
    · simp
    · have bounds := ih h
      simp only [List.length_cons]
      omega

def startOffset (xs : List α) (b : Nat) :=
  (xs.filter (fun x => decide (key x < b))).length

theorem startOffset_succ (xs : List α) (b : Nat) :
    startOffset key xs (b+1) = cursor key (startOffset key xs) xs b := by
  unfold cursor startOffset
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    simp only [Nat.lt_succ_iff] at ih ⊢
    rcases lt_trichotomy (key x) b with h | h | h
    · simp [h, Nat.le_of_lt h, Nat.ne_of_lt h, ih, Nat.add_right_comm]
    · simp [h, ih, Nat.add_assoc]
    · simp [Nat.not_lt_of_ge (Nat.le_of_lt h), Nat.not_le_of_lt h, Ne.symm (Nat.ne_of_lt h), ih]

theorem representable (xs : List α) (b : Nat) (fits : xs.length ≤ 65535) :
    startOffset key xs b ≤ 65535 := (List.length_filter_le ..).trans fits

end BackwardFill
