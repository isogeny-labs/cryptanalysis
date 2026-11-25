import Lean

/-!
The sign-packed table groups an encoded point key `k` by `(k / 2, k % 2)`.
This model proves first-inserted payload semantics for every insertion stream,
including duplicate keys. It models the logical map, not probing or runtime.
-/

namespace SignPacked

abbrev Flat := Nat → Option Nat
abbrev Packed := Nat → Nat → Option Nat

def first (old : Option Nat) (payload : Nat) : Option Nat :=
  old.orElse fun _ => some payload

def lookup (table : Packed) (key : Nat) : Option Nat :=
  table (key / 2) (key % 2)

def flatInsert (table : Flat) (key payload : Nat) : Flat :=
  fun query => if query = key then first (table query) payload else table query

def packedInsert (table : Packed) (key payload : Nat) : Packed :=
  fun x sign =>
    if x = key / 2 ∧ sign = key % 2 then
      first (table x sign) payload
    else table x sign

theorem encoded_point_key (x parity : Nat) (hparity : parity < 2) :
    (2 * x + parity) / 2 = x ∧ (2 * x + parity) % 2 = parity := by
  omega

theorem encoded_key_fits_u32 (x parity : Nat)
    (hx : x < 2 ^ 31) (hparity : parity < 2) :
    2 * x + parity < 2 ^ 32 := by
  omega

theorem split_key_injective {a b : Nat}
    (hx : a / 2 = b / 2) (hs : a % 2 = b % 2) : a = b := by
  omega

theorem insert_preserves_lookup (table : Packed) (key payload query : Nat) :
    lookup (packedInsert table key payload) query =
      flatInsert (lookup table) key payload query := by
  have split : (query / 2 = key / 2 ∧ query % 2 = key % 2) ↔ query = key := by
    constructor
    · intro h
      exact split_key_injective h.1 h.2
    · intro h
      subst query
      exact ⟨rfl, rfl⟩
  simp [lookup, packedInsert, flatInsert, split]

theorem fold_preserves_lookup (stream : List (Nat × Nat))
    (packed : Packed) (flat : Flat)
    (initial : ∀ key, lookup packed key = flat key) :
    ∀ key,
      lookup (stream.foldl (fun table item => packedInsert table item.1 item.2) packed) key =
        (stream.foldl (fun table item => flatInsert table item.1 item.2) flat) key := by
  induction stream generalizing packed flat with
  | nil =>
      intro key
      simpa using initial key
  | cons item rest ih =>
      intro key
      simp only [List.foldl_cons]
      apply ih
      intro query
      rw [insert_preserves_lookup]
      simp [flatInsert, initial]

theorem exact_first_payloads (stream : List (Nat × Nat)) (key : Nat) :
    lookup (stream.foldl (fun table item => packedInsert table item.1 item.2)
      (fun _ _ => none)) key =
    (stream.foldl (fun table item => flatInsert table item.1 item.2)
      (fun _ => none)) key := by
  apply fold_preserves_lookup
  intro query
  rfl

end SignPacked
