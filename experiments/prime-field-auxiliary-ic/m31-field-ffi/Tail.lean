import Mathlib

/-! Index and padding invariants for the four-lane partial tile in m31.cpp. -/
namespace M31Tail

def vectors (count : ℕ) := count / 4 + if count % 4 = 0 then 0 else 1
def last (count : ℕ) := if count % 4 = 0 then 4 else count % 4

theorem dimensions {count : ℕ} (pos : 0 < count) (cap : count ≤ 256) :
    1 ≤ vectors count ∧ vectors count ≤ 64 ∧
    1 ≤ last count ∧ last count ≤ 4 ∧
    4 * (vectors count - 1) + last count = count := by
  unfold vectors last
  split <;> omega

/-- An unpadded vector touches four live words. On the final vector only
the first 'last count' words are accessed in caller storage. -/
theorem valid_lane {count j k : ℕ} (pos : 0 < count) (cap : count ≤ 256)
    (row : j < vectors count) (lane : k < 4) :
    4*j+k < count ↔ j+1 < vectors count ∨ k < last count := by
  obtain ⟨_, _, _, _, _⟩ := dimensions pos cap
  omega

/-- Every caller index has one vector position and every live vector position
maps back to the same caller index. -/
theorem position {count i : ℕ} (hi : i < count) :
    i / 4 < vectors count ∧ i % 4 < 4 ∧ 4*(i/4)+i%4 = i := by
  unfold vectors
  split <;> omega

theorem unique_position {j k i : ℕ} (hk : k < 4) (h : 4*j+k = i) :
    j = i/4 ∧ k = i%4 := by omega

/-- For up to 64 leaves both heap children are inside its 128 slots. -/
theorem heap_children {n i : ℕ} (cap : n ≤ 64) (internal : i < n) :
    2*i < 128 ∧ 2*i+1 < 128 := by omega

theorem heap_leaf {n j : ℕ} (cap : n ≤ 64) (row : j < n) : n+j < 128 := by omega

/-- Applying pointwise inversion to the padded input and retaining its live
prefix returns the unpadded inverses, including totalized inversion at zero. -/
theorem discard_padding {F : Type*} [Field F] (xs : List F) (pad : ℕ) :
    ((xs ++ List.replicate pad 1).map (fun x => x⁻¹)).take xs.length =
      xs.map (fun x => x⁻¹) := by
  simp


end M31Tail
