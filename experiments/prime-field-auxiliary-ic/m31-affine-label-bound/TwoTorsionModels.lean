import Mathlib

namespace M31TwoTorsionModels

variable {K : Type*} [Field K] [DecidableEq K]

/-- B y² = x³ + A x² + x in monic coordinates X=B x, Y=B² y. -/
def model (A B : K) : WeierstrassCurve.Affine K := ⟨0, A*B, 0, B^2, 0⟩

omit [DecidableEq K] in
theorem coordinates (A B x y : K) (hB : B ≠ 0) :
    B*y^2 = x^3 + A*x^2 + x ↔
      (model A B).Equation (B*x) (B^2*y) := by
  rw [WeierstrassCurve.Affine.equation_iff]
  simp only [model, zero_mul, add_zero]
  constructor
  · intro h
    linear_combination B^3*h
  · intro h
    apply (mul_left_cancel₀ (pow_ne_zero 3 hB) : B^3 * _ = B^3 * _ → _)
    linear_combination h

theorem evenCard (A B : K) (hB : B ≠ 0) : 2 ∣ Nat.card (model A B).Point := by
  have ns : (model A B).Nonsingular 0 0 := by
    rw [WeierstrassCurve.Affine.nonsingular_zero]
    exact ⟨rfl, Or.inr (pow_ne_zero 2 hB)⟩
  let P : (model A B).Point := .some 0 0 ns
  have nz : P ≠ 0 := WeierstrassCurve.Affine.Point.some_ne_zero ns
  have twice : (2 : ℕ) • P = 0 := by
    rw [two_nsmul]
    apply WeierstrassCurve.Affine.Point.add_self_of_Y_eq
    simp [WeierstrassCurve.Affine.negY, model]
  have order : addOrderOf P = 2 := by
    rcases (Nat.dvd_prime Nat.prime_two).mp
      (addOrderOf_dvd_iff_nsmul_eq_zero.mpr twice) with one | two
    · exact (nz (AddMonoid.addOrderOf_eq_one_iff.mp one)).elim
    · exact two
  exact order ▸ addOrderOf_dvd_natCard P

theorem excludes (A B : K) (hB : B ≠ 0) :
    Nat.card (model A B).Point ∉ ([2147505293, 2147506201, 2147462003, 2147461095] : List ℕ) := by
  intro h
  have even := evenCard A B hB
  simp only [List.mem_cons, List.not_mem_nil, or_false] at h
  rcases h with h | h | h | h <;> rw [h] at even <;> omega

/-- The trace recurrence modulo two for odd p and odd initial trace.
Since p^k+1 is even, this is also the parity of the extension cardinality. -/
def traceParity : Nat → ZMod 2
  | 0 => 0
  | 1 => 1
  | n+2 => traceParity (n+1) + traceParity n

theorem periodThree (k : Nat) : traceParity (k+3) = traceParity k := by
  change (traceParity (k+1) + traceParity k) + traceParity (k+1) = _
  have two : (2 : ZMod 2) = 0 := by decide
  linear_combination traceParity (k+1) * two

theorem evenExtension (k : Nat) : traceParity k = 0 ↔ 3 ∣ k := by
  induction k using Nat.strong_induction_on with
  | h k ih =>
    rcases k with _ | _ | _ | k
    · decide
    · decide
    · decide
    · rw [periodThree, ih k (by omega)]
      omega

omit [DecidableEq K]

/-- Translating a root to zero gives a Montgomery model in monic
coordinates when the derivative there is a nonzero square. -/
theorem rootModel (a b r B x y : K) (root : r^3+a*r+b=0)
    (deriv : B^2=3*r^2+a) (nz : B ≠ 0) :
    (model (3*r/B) B).Equation (x-r) y ↔ y^2=x^3+a*x+b := by
  rw [WeierstrassCurve.Affine.equation_iff]
  simp only [model, zero_mul, add_zero, div_mul_cancel₀ _ nz, deriv]
  constructor <;> intro h <;> first | linear_combination h + root | linear_combination h - root

/-- In odd characteristic, a Weierstrass change to a monic Montgomery
model forces the translation parameter to be a root with square derivative. -/
theorem necessaryRoot (a b A B : K) (C : WeierstrassCurve.VariableChange K)
    (oddChar : (2 : K) ≠ 0)
    (eqn : C • (⟨0,0,0,a,b⟩ : WeierstrassCurve K) = model A B) :
    C.r^3+a*C.r+b=0 ∧ IsSquare (3*C.r^2+a) := by
  have one := congrArg WeierstrassCurve.a₁ eqn
  have three := congrArg WeierstrassCurve.a₃ eqn
  have four := congrArg WeierstrassCurve.a₄ eqn
  have six := congrArg WeierstrassCurve.a₆ eqn
  simp [WeierstrassCurve.variableChange_a₁, model, oddChar] at one
  simp [WeierstrassCurve.variableChange_a₃, model, oddChar] at three
  simp [WeierstrassCurve.variableChange_a₄, model, one, three] at four
  simp [WeierstrassCurve.variableChange_a₆, model, three] at six
  constructor
  · linear_combination six
  · refine ⟨(C.u : K)^2 * B, ?_⟩
    have h := congrArg (fun z : K => (C.u : K)^4 * z) four
    rw [← mul_assoc, mul_inv_cancel₀ (pow_ne_zero 4 C.u.ne_zero), one_mul] at h
    linear_combination h

/-- For x different from zero, the standard degree-two quotient coordinates
satisfy the curve equation with coefficients -2a and a²-4c. -/
theorem quotientEquation (a c x y : K) (hx : x ≠ 0)
    (onCurve : y^2 = x^3+a*x^2+c*x) :
    let X := x+a+c/x
    let Y := y*(1-c/x^2)
    Y^2 = X^3-2*a*X^2+(a^2-4*c)*X := by
  dsimp only
  rw [mul_pow, onCurve]
  field_simp
  ring

/-- If the other two roots after translation are u and v, the quotient's
linear coefficient is (u-v)². This identifies the monic Montgomery model. -/
theorem splitQuotientModel (u v : K) (distinct : u ≠ v) :
    (⟨0,2*(u+v),0,(u+v)^2-4*(u*v),0⟩ : WeierstrassCurve.Affine K) =
    model (2*(u+v)/(u-v)) (u-v) := by
  have nz : u-v ≠ 0 := sub_ne_zero.mpr distinct
  unfold model
  rw [div_mul_cancel₀ _ nz]
  congr 1
  ring

end M31TwoTorsionModels
