import Lean

/-!
The collector may suppress a fully computed point only if its x-coordinate is
absent from an exact index. These statements preserve the first payload found
in scan order, including when candidates are group identities (`none`).
The premise is discharged by exact lookup of the sign-packed Rust x slots;
it does not assert anything about the measured runtime.
-/

namespace XFilter

def reject {α : Type} (x : α → Nat) (mayX : Nat → Bool) : Option α → Option α
  | none => none
  | some p => if mayX (x p) then some p else none

def firstHit {α β : Type} (lookup : Option α → Option β) : List (Option α) → Option β
  | [] => none
  | p :: ps => match lookup p with
    | some value => some value
    | none => firstHit lookup ps

theorem lookup_reject {α β : Type} (x : α → Nat) (mayX : Nat → Bool)
    (lookup : Option α → Option β) (empty : lookup none = none)
    (exact : ∀ p, mayX (x p) = false → lookup (some p) = none)
    (p : Option α) : lookup (reject x mayX p) = lookup p := by
  cases p with
  | none => simp [reject]
  | some q =>
    cases h : mayX (x q) with
    | false => simp [reject, h, exact q h, empty]
    | true => simp [reject, h]

theorem firstHit_reject {α β : Type} (x : α → Nat) (mayX : Nat → Bool)
    (lookup : Option α → Option β) (empty : lookup none = none)
    (exact : ∀ p, mayX (x p) = false → lookup (some p) = none)
    (candidates : List (Option α)) :
    firstHit lookup (candidates.map (reject x mayX)) = firstHit lookup candidates := by
  induction candidates with
  | nil => rfl
  | cons p ps ih =>
    simp only [List.map_cons, firstHit]
    rw [lookup_reject x mayX lookup empty exact p]
    cases lookup p <;> simp [ih]

end XFilter
