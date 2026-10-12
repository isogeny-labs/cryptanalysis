import Std

/-! Exact composition law for the binary-controlled Frobenius selector.
In the experiment, `step` is field squaring and each listed weight is a
power of two. The Boolean circuit implements `selectOrbit` with XOR/AND muxes.
-/
namespace BinaryFrobenius

universe u
variable {F : Type u}

def power (step : F → F) : Nat → F → F
  | 0, x => x
  | n + 1, x => step (power step n x)

theorem power_add (step : F → F) (m n : Nat) (x : F) :
    power step (m + n) x = power step m (power step n x) := by
  induction m with
  | zero => simp [power]
  | succ m ih =>
      simp only [Nat.succ_add, power]
      rw [ih]

def selectedExponent : List (Nat × Bool) → Nat
  | [] => 0
  | (weight, take) :: tail =>
      selectedExponent tail + (if take then weight else 0)

def selectOrbit (step : F → F) : List (Nat × Bool) → F → F
  | [], x => x
  | (weight, take) :: tail, x =>
      selectOrbit step tail (if take then power step weight x else x)

theorem selectOrbit_correct (step : F → F) :
    ∀ choices x, selectOrbit step choices x =
      power step (selectedExponent choices) x := by
  intro choices
  induction choices with
  | nil => intro x; rfl
  | cons head tail ih =>
      rcases head with ⟨weight, take⟩
      intro x
      cases take with
      | false => simpa [selectOrbit, selectedExponent] using ih x
      | true =>
          simpa [selectOrbit, selectedExponent, power_add] using
            (ih (power step weight x))

def selectFiber (values : Fin 4 → F) (low high : Bool) : F :=
  if high then (if low then values 3 else values 2)
  else (if low then values 1 else values 0)

theorem binary_target_correct (step : F → F) (values : Fin 4 → F)
    (low high : Bool) (choices : List (Nat × Bool)) :
    selectOrbit step choices (selectFiber values low high) =
      power step (selectedExponent choices) (selectFiber values low high) :=
  selectOrbit_correct step choices (selectFiber values low high)

#print axioms BinaryFrobenius.binary_target_correct

end BinaryFrobenius
