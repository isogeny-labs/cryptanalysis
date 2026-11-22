import Mathlib

/-!
An abstract reduction criterion: if every integral relation has even
coefficients and the ambient group has no 2-torsion, then there is no
nonzero integral relation. The arithmetic experiment supplies the parity
premise for its 16 qualifying point pairs.
-/

theorem parity_from_two_independent_reductions
    {G : Type*} [AddCommGroup G] (P Q : G)
    (reduce : G →+ (ZMod 2 × ZMod 2))
    (hP : reduce P = ((1 : ZMod 2), (0 : ZMod 2)))
    (hQ : reduce Q = ((0 : ZMod 2), (1 : ZMod 2))) :
    ∀ a b : ℤ, a • P + b • Q = 0 → Even a ∧ Even b := by
  intro a b hab
  have hz : ((a : ZMod 2), (b : ZMod 2)) = (0, 0) := by
    have h := congrArg reduce hab
    simpa [map_add, map_zsmul, hP, hQ, zsmul_eq_mul] using h
  constructor
  · apply even_iff_two_dvd.mpr
    exact (ZMod.intCast_zmod_eq_zero_iff_dvd a 2).mp (congrArg Prod.fst hz)
  · apply even_iff_two_dvd.mpr
    exact (ZMod.intCast_zmod_eq_zero_iff_dvd b 2).mp (congrArg Prod.snd hz)

theorem parity_from_exponent_two_quotient
    {G H : Type*} [AddCommGroup G] [AddCommGroup H]
    (P Q : G) (reduce : G →+ H)
    (hexp : ∀ x : H, (2 : ℤ) • x = 0)
    (hP : reduce P ≠ 0) (hQ : reduce Q ≠ 0)
    (hPQ : reduce P + reduce Q ≠ 0) :
    ∀ a b : ℤ, a • P + b • Q = 0 → Even a ∧ Even b := by
  have hsmul (n : ℤ) (x : H) : n • x = (n % 2) • x := by
    have hn : n = 2 * (n / 2) + n % 2 := by omega
    conv_lhs => rw [hn]
    rw [add_zsmul, mul_zsmul, hexp, zero_add]
  intro a b hab
  have hz : a • reduce P + b • reduce Q = 0 := by
    simpa using congrArg reduce hab
  rw [hsmul a (reduce P), hsmul b (reduce Q)] at hz
  have ha : a % 2 = 0 ∨ a % 2 = 1 := by omega
  have hb : b % 2 = 0 ∨ b % 2 = 1 := by omega
  rcases ha with ha | ha <;> rcases hb with hb | hb
  · constructor <;> apply even_iff_two_dvd.mpr <;> omega
  · simp [ha, hb] at hz
    exact False.elim (hQ hz)
  · simp [ha, hb] at hz
    exact False.elim (hP hz)
  · simp [ha, hb] at hz
    exact False.elim (hPQ hz)

theorem auxiliary_mod2_independence
    {G : Type*} [AddCommGroup G] (P Q : G)
    (h2 : ∀ x : G, (2 : ℤ) • x = 0 → x = 0)
    (hpar : ∀ a b : ℤ, a • P + b • Q = 0 → Even a ∧ Even b) :
    ∀ a b : ℤ, a • P + b • Q = 0 → a = 0 ∧ b = 0 := by
  intro a b hab
  let R : ℤ → ℤ → Prop := fun a b => a • P + b • Q = 0
  have half : ∀ a b : ℤ, R (2 * a) (2 * b) → R a b := by
    intro a b h
    apply h2
    simpa [R, mul_zsmul, smul_add] using h
  have descend : ∀ n : ℕ, ∀ a b : ℤ,
      a.natAbs + b.natAbs = n → R a b → a = 0 ∧ b = 0 := by
    intro n
    induction n using Nat.strong_induction_on with
    | h n ih =>
      intro a b hn hr
      obtain ⟨⟨a', ha⟩, ⟨b', hb⟩⟩ := hpar a b hr
      have ha2 : a = 2 * a' := by omega
      have hb2 : b = 2 * b' := by omega
      have hr' : R a' b' := half a' b' (by simpa [ha2, hb2] using hr)
      by_cases hz : a = 0 ∧ b = 0
      · exact hz
      have hlt : a'.natAbs + b'.natAbs < n := by
        simp only [ha2, hb2] at hn hz
        omega
      obtain ⟨ha0, hb0⟩ := ih _ hlt a' b' rfl hr'
      constructor <;> omega
  exact descend (a.natAbs + b.natAbs) a b rfl hab

theorem independent_of_mod2_reduction
    {G : Type*} [AddCommGroup G] (P Q : G)
    (h2 : ∀ x : G, (2 : ℤ) • x = 0 → x = 0)
    (reduce : G →+ (ZMod 2 × ZMod 2))
    (hP : reduce P = ((1 : ZMod 2), (0 : ZMod 2)))
    (hQ : reduce Q = ((0 : ZMod 2), (1 : ZMod 2))) :
    ∀ a b : ℤ, a • P + b • Q = 0 → a = 0 ∧ b = 0 :=
  auxiliary_mod2_independence P Q h2
    (parity_from_two_independent_reductions P Q reduce hP hQ)

theorem independent_of_exponent_two_quotient
    {G H : Type*} [AddCommGroup G] [AddCommGroup H]
    (P Q : G)
    (h2 : ∀ x : G, (2 : ℤ) • x = 0 → x = 0)
    (reduce : G →+ H)
    (hexp : ∀ x : H, (2 : ℤ) • x = 0)
    (hP : reduce P ≠ 0) (hQ : reduce Q ≠ 0)
    (hPQ : reduce P + reduce Q ≠ 0) :
    ∀ a b : ℤ, a • P + b • Q = 0 → a = 0 ∧ b = 0 :=
  auxiliary_mod2_independence P Q h2
    (parity_from_exponent_two_quotient P Q reduce hexp hP hQ hPQ)

#print axioms auxiliary_mod2_independence
#print axioms parity_from_two_independent_reductions
#print axioms independent_of_mod2_reduction
#print axioms parity_from_exponent_two_quotient
#print axioms independent_of_exponent_two_quotient
