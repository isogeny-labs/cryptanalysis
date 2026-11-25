import Mathlib.Tactic

namespace FiberAddress

/-- Read the low bit at the leaf, then move towards the terminal. -/
def address {α : Type*} (parent : α → α) (bit : α → Nat) : Nat → α → Nat
  | 0, _ => 0
  | n+1, x => 2 * address parent bit n (parent x) + bit x

/-- Descend using the low bit of the requested slot for the last edge. -/
def rootAt {α : Type*} (child : α → Nat → α) (terminal : α) : Nat → Nat → α
  | 0, _ => terminal
  | n+1, i => child (rootAt child terminal n (i / 2)) (i % 2)

theorem address_rootAt {α : Type*} (parent : α → α) (bit : α → Nat)
    (child : α → Nat → α) (terminal : α)
    (depth : Nat)
    (back : ∀ k < depth, ∀ j < 2^k, ∀ b < 2,
      parent (child (rootAt child terminal k j) b) = rootAt child terminal k j)
    (label : ∀ k < depth, ∀ j < 2^k, ∀ b < 2,
      bit (child (rootAt child terminal k j) b) = b)
    (n i : Nat) (level : n ≤ depth) (bound : i < 2 ^ n) :
    address parent bit n (rootAt child terminal n i) = i := by
  induction n generalizing i with
  | zero =>
    simp only [pow_zero] at bound
    simp only [address]
    omega
  | succ n ih =>
    have h : i / 2 < 2 ^ n := by
      rw [pow_succ] at bound
      omega
    have hn : n < depth := by omega
    simp only [rootAt, address, back n hn _ h _ (Nat.mod_lt _ (by decide)),
      label n hn _ h _ (Nat.mod_lt _ (by decide)), ih _ (by omega) h]
    omega

end FiberAddress
