import XFilter

/-!
Logical x-bitmap invariant for the collector. Marking a hashed bit for every
inserted x permits collisions but cannot reject an inserted x. Combined with
`XFilter.firstHit_reject`, it preserves the first accepted pair payload.
The Rust u64 indexing and table insertion are checked separately; this proof
models their intended state transition, not machine code or runtime.
-/

namespace Bloom

def mark (bits : Nat → Bool) (index : Nat) : Nat → Bool :=
  fun query => if query = index then true else bits query

def bitmap (hash : Nat → Nat) : List Nat → Nat → Bool
  | [] => fun _ => false
  | x :: xs => mark (bitmap hash xs) (hash x)

theorem inserted_bit_set (hash : Nat → Nat) (xs : List Nat) (x : Nat)
    (member : x ∈ xs) : bitmap hash xs (hash x) = true := by
  induction xs with
  | nil => cases member
  | cons y ys ih =>
    rcases List.mem_cons.mp member with same | rest
    · subst x
      simp [bitmap, mark]
    · simp only [bitmap, mark]
      split
      · rfl
      · exact ih rest

theorem first_payload_preserved {α β : Type} (x : α → Nat)
    (hash : Nat → Nat) (inserted : List Nat)
    (lookup : Option α → Option β) (empty : lookup none = none)
    (support : ∀ p, lookup (some p) ≠ none → x p ∈ inserted)
    (candidates : List (Option α)) :
    XFilter.firstHit lookup
      (candidates.map (XFilter.reject x (fun q => bitmap hash inserted (hash q)))) =
    XFilter.firstHit lookup candidates := by
  apply XFilter.firstHit_reject x (fun q => bitmap hash inserted (hash q)) lookup empty
  · intro p missing
    by_cases hit : lookup (some p) = none
    · exact hit
    · have present := inserted_bit_set hash inserted (x p) (support p hit)
      rw [missing] at present
      cases present

end Bloom
