import Std

namespace M31SubsetFrontier.Payload

/-- Signed basis indices are numbered consecutively in positive/negative pairs. -/
def flip (i : Nat) := 2 * (i / 2) + (1 - i % 2)

private theorem flip_twice (i : Nat) : flip (flip i) = i := by unfold flip; omega
private theorem flip_base (i : Nat) : flip i / 2 = i / 2 := by unfold flip; omega

def ordered (i j : Nat) := if i ≤ j then (i, j) else (j, i)
def reverseSigns (p : Nat × Nat) := ordered (flip p.1) (flip p.2)

/-- Looking up the opposite sign twice recovers the original ordered indices. -/
theorem reverse_twice (i j : Nat) (sorted : i ≤ j) :
    reverseSigns (reverseSigns (i,j)) = (i,j) := by
  simp only [reverseSigns, ordered]
  split <;> simp [flip_twice, sorted]
  intro ji
  exact ⟨Nat.le_antisymm ji sorted, Nat.le_antisymm sorted ji⟩

private theorem first_base (i j : Nat) (sorted : i ≤ j) :
    (reverseSigns (i,j)).1 / 2 = i / 2 := by
  simp only [reverseSigns, ordered]
  split <;> simp only [flip_base] <;> unfold flip at * <;> omega

/-- A strict advantage in the first unsigned index preserves the insertion
order between two competing payloads after negating and reordering. -/
theorem collision_order (i j k l : Nat) (ij : i ≤ j) (kl : k ≤ l)
    (earlier : i / 2 < k / 2) :
    (reverseSigns (i,j)).1 < (reverseSigns (k,l)).1 := by
  have h₁ := first_base i j ij
  have h₂ := first_base k l kl
  omega

end M31SubsetFrontier.Payload
