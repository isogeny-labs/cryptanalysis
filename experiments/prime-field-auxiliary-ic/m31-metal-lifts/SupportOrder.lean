import Mathlib.Data.List.Basic

namespace M31SupportOrder

/-- Each extension produces powers of one new prime, in increasing exponent
order, from a single earlier coordinate. An empty list represents the cutoff. -/
abbrev Extension := ℕ → List ℕ

def sequential (steps : List Extension) (values : List ℕ) : List ℕ :=
  match steps with
  | [] => values
  | e :: rest => sequential rest (values ++ values.flatMap e)

def grouped (steps : List Extension) (blocks : List (List ℕ)) : List (List ℕ) :=
  match steps with
  | [] => blocks
  | e :: rest => grouped rest (blocks ++ blocks.map (fun b => b.flatMap e))

private theorem expand_blocks (blocks : List (List ℕ)) (e : Extension) :
    (blocks.map (fun b => b.flatMap e)).flatten = blocks.flatten.flatMap e := by
  induction blocks with
  | nil => rfl
  | cons b bs ih => simp [ih]

/-- Appending the new support blocks preserves the entire original ordered
coordinate stream at every prime, including possibly empty blocks. -/
theorem same_order (steps : List Extension) (blocks : List (List ℕ)) :
    (grouped steps blocks).flatten = sequential steps blocks.flatten := by
  induction steps generalizing blocks with
  | nil => rfl
  | cons e rest ih =>
    simp only [grouped,sequential,ih,List.flatten_append,expand_blocks]

end M31SupportOrder
