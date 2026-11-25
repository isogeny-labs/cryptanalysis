import Mathlib.Tactic

namespace M31SignedPairs

/-- For the two affine secant slopes, the single recovered reciprocal
suffices for both full affine outputs. Equal abscissas use a separate path. -/
theorem signed_secants {K : Type*} [Field K] (x y u v pre post carry : K)
    (h : carry * (pre * (u - x) * post) = 1) :
    let r := carry * pre * post
    let finish := fun (s : K) =>
      let a := s^2 - x - u
      (a, s * (x - a) - y)
    (finish ((v-y)*r), finish ((-v-y)*r)) =
      (finish ((v-y)/(u-x)), finish ((-v-y)/(u-x))) := by
  have hr : (carry * pre * post) * (u-x) = 1 := by
    linear_combination h
  have hi : carry * pre * post = (u-x)⁻¹ := (eq_inv_of_mul_eq_one_left hr)
  simp [hi, div_eq_mul_inv]

section Scan

variable {K : Type*} [Field K]
abbrev Lanes (K : Type*) := Fin 4 → K

/-- Four lane inverses from one inversion, using the saved forward products. -/
def invertFour (a : Lanes K) : Lanes K :=
  let ab := a 0 * a 1
  let abc := ab * a 2
  let t := (abc * a 3)⁻¹
  let u := t * a 3
  let v := u * a 2
  ![v * a 1, v * a 0, u * ab, t * abc]

theorem invertFour_spec (a : Lanes K) (ha : ∀ j, a j ≠ 0) :
    invertFour a = fun j => (a j)⁻¹ := by
  funext j
  fin_cases j <;> simp [invertFour, ha, mul_assoc, mul_comm, mul_left_comm]

variable [DecidableEq K]

/-- Recursion records the forward lane prefix on descent and consumes it
on return, which visits the same entries in reverse. A zero denotes a slot
delegated to the exceptional point-addition path. -/
def scan (a : Lanes K) : List (Fin 4 × K) → Lanes K × List (Option K)
  | [] => (invertFour a, [])
  | (j,d) :: xs =>
    if d = 0 then
      let (back, rest) := scan a xs
      (back, none :: rest)
    else
      let (back, rest) := scan (Function.update a j (a j * d)) xs
      (Function.update back j (back j * d), some (back j * a j) :: rest)

def expected (s : Fin 4 × K) : Option K :=
  if s.2 = 0 then none else some s.2⁻¹

theorem scan_spec (xs : List (Fin 4 × K)) (a : Lanes K) (ha : ∀ j, a j ≠ 0) :
    scan a xs = (fun j => (a j)⁻¹, xs.map expected) := by
  induction xs generalizing a with
  | nil => simp [scan, invertFour_spec a ha]
  | cons slot xs ih =>
    rcases slot with ⟨j,d⟩
    by_cases hd : d = 0
    · simp [scan, hd, ih a ha, expected]
    · let next := Function.update a j (a j * d)
      have hn : ∀ i, next i ≠ 0 := by
        intro i
        by_cases e : i = j <;> simp [next, e, ha, hd]
      have hs := ih next hn
      change scan (Function.update a j (a j * d)) xs = _ at hs
      simp only [scan, hd, ite_false, hs, List.map_cons, expected]
      apply Prod.ext
      · funext i
        by_cases e : i = j <;> simp [next, Function.update, e, hd, mul_comm]
      · simp [next, ha, mul_comm]

end Scan

/-- In the finite-input positive control, subtracting either of two distinct
representatives from their sum returns the other one. -/
theorem two_positive_slots {G : Type*} [AddCommGroup G] (a b : G) (h : a ≠ b) :
    (a+b)+(-a) = b ∧ (a+b)+(-b) = a ∧ (a+b)+(-a) ≠ (a+b)+(-b) := by
  simpa [add_assoc, add_left_comm, add_comm] using Ne.symm h

end M31SignedPairs
