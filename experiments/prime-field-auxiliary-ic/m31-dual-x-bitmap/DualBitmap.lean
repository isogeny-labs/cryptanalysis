import Bloom

/-!
The two projections are necessary conditions for exact x membership. Their
conjunction may admit false positives, but it cannot suppress an inserted x.
Consequently the first successful exact-index payload is unchanged. This is a
statement about the lookup algorithm, not measured time or Rust machine code.
-/

namespace DualBitmap

def mayContain (high low : Nat → Nat) (inserted : List Nat) (x : Nat) : Bool :=
  Bloom.bitmap high inserted (high x) && Bloom.bitmap low inserted (low x)

theorem inserted_mayContain (high low : Nat → Nat) (inserted : List Nat)
    (x : Nat) (member : x ∈ inserted) :
    mayContain high low inserted x = true := by
  simp [mayContain, Bloom.inserted_bit_set high inserted x member,
    Bloom.inserted_bit_set low inserted x member]

theorem first_payload_preserved {α β : Type} (x : α → Nat)
    (high low : Nat → Nat) (inserted : List Nat)
    (lookup : Option α → Option β) (empty : lookup none = none)
    (support : ∀ p, lookup (some p) ≠ none → x p ∈ inserted)
    (candidates : List (Option α)) :
    XFilter.firstHit lookup
      (candidates.map (XFilter.reject x (mayContain high low inserted))) =
    XFilter.firstHit lookup candidates := by
  apply XFilter.firstHit_reject x (mayContain high low inserted) lookup empty
  · intro p missing
    by_cases hit : lookup (some p) = none
    · exact hit
    · have present := inserted_mayContain high low inserted (x p) (support p hit)
      rw [missing] at present
      cases present

end DualBitmap
