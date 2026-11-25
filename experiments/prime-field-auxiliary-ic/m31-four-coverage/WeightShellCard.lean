import Mathlib.Tactic

namespace M31.WeightShellCard

abbrev Digit := Fin 17
-- Digits 0 through 8 denote their own values; 9 through 16 denote -1 through -8.
def magnitude (d : Digit) := if d.val ≤ 8 then d.val else d.val - 8

-- Remaining weight, awaiting the first nonzero digit, still requiring an odd digit.
abbrev State := Option (Fin 9 × Bool × Bool)

def advance : State → Digit → State
  | none, _ => none
  | some (w, first, odd), d =>
    if magnitude d > w.val || (first && decide (8 < d.val)) then none
    else some (⟨w.val - magnitude d, lt_of_le_of_lt (Nat.sub_le ..) w.isLt⟩,
      first && decide (d.val = 0), odd && decide (magnitude d % 2 = 0))

def accept : State → Bool
  | some (w, _, odd) => decide (w.val = 0) && !odd
  | none => false

def reads : (n : ℕ) → State → (Fin n → Digit) → Bool
  | 0, s, _ => accept s
  | n+1, s, v => reads n (advance s (v 0)) (Fin.tail v)

abbrev Shell (n : ℕ) (s : State) := {v : Fin n → Digit // reads n s v = true}

def split (n : ℕ) (s : State) : Shell (n+1) s ≃ Σ d : Digit, Shell n (advance s d) where
  toFun v := ⟨v.val 0, Fin.tail v.val, v.property⟩
  invFun := fun ⟨d, v⟩ => ⟨Fin.cons d v.val, by simpa [reads] using v.property⟩
  left_inv v := Subtype.ext (Fin.cons_self_tail v.val)
  right_inv := by
    rintro ⟨d, ⟨v, hv⟩⟩
    rfl

-- Materialize the previous row once to keep evaluation polynomial in the dimension.
abbrev Row := ℕ × Vector ((ℕ × ℕ) × (ℕ × ℕ)) 9

def build (f : State → ℕ) : Row :=
  (f none, Vector.ofFn (fun w : Fin 9 =>
    ((f (some (w,false,false)), f (some (w,false,true))),
     (f (some (w,true,false)), f (some (w,true,true))))))

def lookup (row : Row) : State → ℕ
  | none => row.1
  | some (w, first, odd) =>
    let p := if first then row.2[w].2 else row.2[w].1
    if odd then p.2 else p.1

theorem lookup_build (f : State → ℕ) (s : State) : lookup (build f) s = f s := by
  rcases s with _ | ⟨w, f₁, f₂⟩
  · rfl
  · cases f₁ <;> cases f₂ <;> simp [lookup, build]

def rows : ℕ → Row
  | 0 => build (fun s => if accept s then 1 else 0)
  | n+1 =>
    let prev := rows n
    build (fun s => ∑ d : Digit, lookup prev (advance s d))

def count (n : ℕ) (s : State) := lookup (rows n) s

theorem card_eq (n : ℕ) (s : State) : Nat.card (Shell n s) = count n s := by
  induction n generalizing s with
  | zero =>
    classical
    cases h : accept s <;> simp [Shell, reads, count, rows, lookup_build, h, Nat.card_eq_fintype_card]
  | succ n ih =>
    rw [Nat.card_congr (split n s), Nat.card_sigma]
    simp only [ih, count, rows, lookup_build]

-- A common divisor divides total weight eight. Thus primitivity here is
-- equivalent to having at least one odd coefficient.
set_option maxRecDepth 10000
set_option maxHeartbeats 2000000

theorem primitive_count : Nat.card (Shell 17 (some (8,true,true))) = 24303744 := by
  rw [card_eq]
  decide +kernel

theorem all_count : Nat.card (Shell 17 (some (8,true,false))) = 24331777 := by
  rw [card_eq]
  decide +kernel

end M31.WeightShellCard
