import Std.Tactic
set_option autoImplicit false
namespace CounterStorage

def resolve {K : Type} [DecidableEq K]
    (index : K → Nat) (cache : Option (K × Nat)) (key : K) : Nat :=
  match cache with
  | none => index key
  | some (cached, i) => if cached = key then i else index key

def bump {A : Type} [DecidableEq A]
    (values : A → Nat) (key : A) (amount : Nat) : A → Nat :=
  fun a => if a = key then values a + amount else values a

/-- Exact-key cache resolution is correct when the cached pair was made from
the canonical index. No pointer bucket, Rust program or thread model is encoded. -/
theorem resolve_index {K : Type} [DecidableEq K]
    (index : K → Nat) (cache : Option (K × Nat)) (key : K)
    (sound : ∀ a i, cache = some (a, i) → i = index a) :
    resolve index cache key = index key := by
  cases cache with
  | none => rfl
  | some entry =>
    rcases entry with ⟨a, i⟩
    have hi := sound a i rfl
    by_cases h : a = key
    · subst key
      simpa [resolve] using hi
    · simp [resolve, h]

/-- On currently indexed keys, a consistent indexed store and exact-key cache
preserve both the overflow guard and every canonical counter after one bump.
Dynamic insertion, Vec bounds, u64 encoding, TLS and the Rust bridge remain
explicitly outside this structural function model. -/
theorem checked_update {K : Type} [DecidableEq K]
    (index : K → Nat) (values : Nat → Nat) (canonical : K → Nat)
    (cache : Option (K × Nat)) (key : K) (amount limit : Nat)
    (injective : ∀ a b, index a = index b → a = b)
    (consistent : ∀ a, values (index a) = canonical a)
    (sound : ∀ a i, cache = some (a, i) → i = index a) :
    ((values (resolve index cache key) + amount ≤ limit) ↔
      (canonical key + amount ≤ limit)) ∧
    (∀ a, bump values (resolve index cache key) amount (index a) =
      bump canonical key amount a) := by
  rw [resolve_index index cache key sound]
  constructor
  · rw [consistent key]
  · intro a
    by_cases h : a = key
    · subst a
      simp [bump, consistent]
    · have different : index a ≠ index key := by
        intro equal
        exact h (injective a key equal)
      simp [bump, h, different, consistent]

end CounterStorage
