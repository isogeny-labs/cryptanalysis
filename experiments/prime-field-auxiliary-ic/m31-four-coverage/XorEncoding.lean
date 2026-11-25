import Mathlib.Data.ZMod.Basic

namespace M31XorEncoding

/-- An xor-valued encoding that preserves every sum must vanish whenever
every source element is a double. The bit index type can have any size. -/
theorem collapse {A ι : Type*} [Add A]
    (halves : ∀ x : A, ∃ y, x = y + y)
    (encode : A → ι → ZMod 2)
    (preserves : ∀ x y, encode (x + y) = encode x + encode y)
    (x : A) : encode x = 0 := by
  obtain ⟨y, rfl⟩ := halves x
  rw [preserves]
  funext i
  change encode y i + encode y i = 0
  rw [← two_mul, show (2 : ZMod 2) = 0 by decide, zero_mul]

theorem ring_collapse {A ι : Type*} [Ring A] (half : A)
    (unit : half + half = 1) (encode : A → ι → ZMod 2)
    (preserves : ∀ x y, encode (x + y) = encode x + encode y)
    (x : A) : encode x = 0 :=
  collapse (fun t => ⟨half * t, by rw [← add_mul, unit, one_mul]⟩) encode preserves x

theorem subgroup {ι : Type*} (encode : ZMod 2147505293 → ι → ZMod 2)
    (preserves : ∀ x y, encode (x + y) = encode x + encode y)
    (x : ZMod 2147505293) : encode x = 0 :=
  ring_collapse 1073752647 (by decide +kernel) encode preserves x

theorem coordinate {ι : Type*} (encode : ZMod 2147483647 → ι → ZMod 2)
    (preserves : ∀ x y, encode (x + y) = encode x + encode y)
    (x : ZMod 2147483647) : encode x = 0 :=
  ring_collapse 1073741824 (by decide +kernel) encode preserves x

end M31XorEncoding
