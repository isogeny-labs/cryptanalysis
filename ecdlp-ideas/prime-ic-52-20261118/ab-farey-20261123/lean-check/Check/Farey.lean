import Mathlib

/-!
# The small-rational-height (a/b) factor base: what is machine-checked

Two claims from PROTOCOL.json are formalised here.

## Part 1 — `sum_repCount`, `mean_shape_blind` (the load-bearing one)

For a finite abelian group `G`, a factor base `F ⊆ G` and an arity `m`, let
`repCount F m g` be the number of ordered `m`-tuples of points of `F` whose sum
is `g`.  Then `∑ g, repCount F m g = |F|^m`, so the mean of `repCount` over the
group is `|F|^m / |G|` **for every shape of `F`**.  Any two factor bases with the
same cardinality have the same total (and hence the same mean) representation
count.  This is the precise sense in which "choosing the right a/b's" cannot buy
relations: it can move mass between targets, not create it.

## Part 2 — `farey_card`

`#{(a,b) : 1 ≤ a ≤ b ≤ B, gcd(a,b) = 1} = ∑_{b ≤ B} φ(b)`.  This is the exact
size of the base before the two involutions `x ↦ -x`, `x ↦ 1/x`; the generator
in `abgen.py` asserts the quotient count `4·Φ(B) − 1` against brute force.

## Part 3 — `box_product`

The Jochemsz–May box product of the `2m`-variable `a/b` encoding at equal `|F|`
equals that of the `m`-variable interval encoding, because the height advantage
`B ~ sqrt |F|` is exactly canceled by the doubled variable count.
-/

open Finset

namespace ABFarey

/-! ## Part 1: the representation count is shape-blind -/

variable {G : Type*} [AddCommMonoid G] [DecidableEq G] [Fintype G]

/-- All ordered `m`-tuples of elements of `F`. -/
def tuples (F : Finset G) (m : ℕ) : Finset (Fin m → G) :=
  Fintype.piFinset (fun _ : Fin m => F)

/-- The exact (ordered) representation function of the factor base `F`. -/
def repCount (F : Finset G) (m : ℕ) (g : G) : ℕ :=
  ((tuples F m).filter (fun v => ∑ i, v i = g)).card

omit [AddCommMonoid G] [DecidableEq G] [Fintype G] in
theorem card_tuples (F : Finset G) (m : ℕ) : (tuples F m).card = F.card ^ m := by
  simp [tuples, Fintype.card_piFinset]

/-- **Total representation count is `|F|^m`, for every factor base.** -/
theorem sum_repCount (F : Finset G) (m : ℕ) :
    ∑ g : G, repCount F m g = F.card ^ m := by
  have H : ∀ v ∈ tuples F m, (∑ i, v i) ∈ (univ : Finset G) := by simp
  simp only [repCount]
  rw [← card_tuples F m]
  exact (Finset.card_eq_sum_card_fiberwise (s := tuples F m) (t := univ)
    (f := fun v : Fin m → G => ∑ i, v i) H).symm

/-- **Shape blindness.** Equal-sized factor bases have equal total yield, so no
choice of `{a/b}` can raise the expected relation yield at fixed `|F|`. -/
theorem mean_shape_blind (F₁ F₂ : Finset G) (m : ℕ) (h : F₁.card = F₂.card) :
    ∑ g : G, repCount F₁ m g = ∑ g : G, repCount F₂ m g := by
  rw [sum_repCount, sum_repCount, h]

/-! ## Part 2: the Farey pair count -/

/-- For `b ≥ 1`, exactly `φ(b)` of the `a ∈ [1,b]` are coprime to `b`:
`a ↦ b - a` carries `{a < b}` onto `{1 ≤ a ≤ b}` and preserves coprimality. -/
theorem card_coprime_Icc (b : ℕ) :
    ((Icc 1 b).filter (fun a => a.Coprime b)).card = b.totient := by
  rw [Nat.totient_eq_card_coprime]
  have himg : ((range b).filter (fun a => b.Coprime a)).image (fun a => b - a)
      = (Icc 1 b).filter (fun a => a.Coprime b) := by
    ext c
    simp only [mem_image, mem_filter, mem_range, mem_Icc]
    constructor
    · rintro ⟨a, ⟨halt, hcop⟩, rfl⟩
      exact ⟨⟨by omega, by omega⟩,
        (Nat.coprime_self_sub_left (le_of_lt halt)).mpr hcop.symm⟩
    · rintro ⟨⟨hc1, hc2⟩, hcop⟩
      exact ⟨b - c, ⟨by omega, ((Nat.coprime_self_sub_left hc2).mpr hcop).symm⟩, by omega⟩
  rw [← himg, Finset.card_image_of_injOn]
  intro x hx y hy h
  simp only [mem_coe, mem_filter, mem_range] at hx hy
  have h' : b - x = b - y := h
  omega

/-- Primitive pairs with `1 ≤ a ≤ b ≤ B`: the base before the sign and
reciprocal involutions. -/
def fareyPairs (B : ℕ) : Finset (ℕ × ℕ) :=
  ((Icc 1 B) ×ˢ (Icc 1 B)).filter (fun p => p.1 ≤ p.2 ∧ p.1.Coprime p.2)

/-- **`#fareyPairs B = ∑_{b ≤ B} φ(b)`**: split off the pairs with `b = B+1`. -/
theorem farey_card (B : ℕ) :
    (fareyPairs B).card = ∑ b ∈ Icc 1 B, b.totient := by
  induction B with
  | zero => simp [fareyPairs]
  | succ B ih =>
    set newpairs : Finset (ℕ × ℕ) :=
      ((Icc 1 (B + 1)).filter (fun a => a.Coprime (B + 1))).image (fun a => (a, B + 1))
      with hnew
    have hmem_old : ∀ p : ℕ × ℕ, p ∈ fareyPairs B ↔
        1 ≤ p.1 ∧ p.1 ≤ p.2 ∧ p.2 ≤ B ∧ p.1.Coprime p.2 := by
      intro p
      obtain ⟨a, b⟩ := p
      simp only [fareyPairs, mem_filter, mem_product, mem_Icc]
      constructor
      · rintro ⟨⟨⟨h1, _⟩, ⟨_, h3⟩⟩, hab, hcop⟩
        exact ⟨h1, hab, h3, hcop⟩
      · rintro ⟨h1, hab, h2, hcop⟩
        exact ⟨⟨⟨h1, by omega⟩, ⟨by omega, h2⟩⟩, hab, hcop⟩
    have hmem_new : ∀ p : ℕ × ℕ, p ∈ newpairs ↔
        p.2 = B + 1 ∧ 1 ≤ p.1 ∧ p.1 ≤ B + 1 ∧ p.1.Coprime (B + 1) := by
      intro p
      obtain ⟨a, b⟩ := p
      rw [hnew]
      simp only [mem_image, mem_filter, mem_Icc, Prod.mk.injEq]
      constructor
      · rintro ⟨x, ⟨⟨hx1, hx2⟩, hcop⟩, rfl, rfl⟩
        exact ⟨rfl, hx1, hx2, hcop⟩
      · rintro ⟨rfl, h1, h2, hcop⟩
        exact ⟨a, ⟨⟨h1, h2⟩, hcop⟩, rfl, rfl⟩
    have hstep : fareyPairs (B + 1) = fareyPairs B ∪ newpairs := by
      ext p
      obtain ⟨a, b⟩ := p
      simp only [fareyPairs, mem_filter, mem_product, mem_Icc, mem_union]
      constructor
      · rintro ⟨⟨⟨h1, _⟩, ⟨_, hb2⟩⟩, hab, hcop⟩
        by_cases hb : b = B + 1
        · exact Or.inr (hmem_new _ |>.mpr ⟨hb, h1, by omega, by rwa [hb] at hcop⟩)
        · exact Or.inl ⟨⟨⟨h1, by omega⟩, ⟨by omega, by omega⟩⟩, hab, hcop⟩
      · intro hp
        rcases hp with hp | hp
        · obtain ⟨⟨⟨h1, _⟩, ⟨_, hb2⟩⟩, hab, hcop⟩ := hp
          exact ⟨⟨⟨h1, by omega⟩, ⟨by omega, by omega⟩⟩, hab, hcop⟩
        · rw [hmem_new] at hp
          obtain ⟨hb, h1, h2, hcop⟩ := hp
          subst hb
          exact ⟨⟨⟨h1, by omega⟩, ⟨by omega, le_rfl⟩⟩, by omega, hcop⟩
    have hdisj : Disjoint (fareyPairs B) newpairs := by
      rw [Finset.disjoint_left]
      intro p hp hq
      rw [hmem_old] at hp
      rw [hmem_new] at hq
      omega
    have himg : newpairs.card = Nat.totient (B + 1) := by
      rw [hnew, Finset.card_image_of_injective _ (fun x y h => by simpa using h),
        card_coprime_Icc]
    rw [hstep, Finset.card_union_of_disjoint hdisj, ih, himg,
      Finset.sum_Icc_succ_top (by omega)]

/-! ## Part 3: the height advantage is cancelled by the doubled variables -/

/-- At equal `|F| = B*B` the `2m`-variable `a/b` box product, with `d` the
individual degree in each of the `2m` coordinates, equals the `m`-variable
interval product. -/
theorem box_product (B m d : ℕ) : (B * B) ^ (m * d) = B ^ (2 * m * d) := by ring

end ABFarey

/-! ## Part 4: the one non-uniformity in `r`, proved

Section 6 of the report retracts a height law and replaces it with: the only
non-uniformity in the representation count is the trivially known one, that a
target which is itself a base element has at least `|F|` ordered representations
at `m = 3` (`{R, P, -P}` for every `P`).  That is what the measurement sees as
an in-base spike; here it is a theorem.
-/

namespace ABFarey

section Spike

variable {H : Type*} [AddCommGroup H] [DecidableEq H] [Fintype H]

/-- The triple `(R, P, -P)`. -/
def spikeTriple (R P : H) : Fin 3 → H := ![R, P, -P]

lemma spikeTriple_inj (R : H) : Function.Injective (spikeTriple R) := by
  intro P Q h
  have h1 := congrFun h 1
  simpa [spikeTriple] using h1

lemma spikeTriple_mem (F : Finset H) (R : H) (hR : R ∈ F)
    (hneg : ∀ x ∈ F, -x ∈ F) {P : H} (hP : P ∈ F) :
    spikeTriple R P ∈ tuples F 3 := by
  simp only [tuples, Fintype.mem_piFinset]
  intro i
  fin_cases i
  · simpa [spikeTriple] using hR
  · simpa [spikeTriple] using hP
  · simpa [spikeTriple] using hneg P hP

omit [DecidableEq H] [Fintype H] in
lemma spikeTriple_sum (R P : H) : (∑ i, spikeTriple R P i) = R := by
  simp [spikeTriple, Fin.sum_univ_three]

/-- **The in-base spike.** A target that is a base element has at least `|F|`
ordered 3-term representations from `F`, for any negation-closed `F`. -/
theorem repCount_three_ge_of_mem (F : Finset H) (R : H) (hR : R ∈ F)
    (hneg : ∀ x ∈ F, -x ∈ F) : F.card ≤ repCount F 3 R := by
  have hinj : Set.InjOn (spikeTriple R) ↑F := fun a _ b _ h => spikeTriple_inj R h
  have hsub : F.image (spikeTriple R) ⊆
      (tuples F 3).filter (fun v => ∑ i, v i = R) := by
    intro v hv
    obtain ⟨P, hP, rfl⟩ := Finset.mem_image.mp hv
    exact Finset.mem_filter.mpr
      ⟨spikeTriple_mem F R hR hneg hP, spikeTriple_sum R P⟩
  calc F.card = (F.image (spikeTriple R)).card := (Finset.card_image_of_injOn hinj).symm
    _ ≤ ((tuples F 3).filter (fun v => ∑ i, v i = R)).card := Finset.card_le_card hsub
    _ = repCount F 3 R := rfl

end Spike

end ABFarey
