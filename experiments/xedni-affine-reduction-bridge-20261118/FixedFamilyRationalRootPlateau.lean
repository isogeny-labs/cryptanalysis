import Mathlib.Tactic

/-! Canonical rational-root data for the frozen xedni coefficient and offset
family, with checked structural implications of a finite bound certificate. -/
namespace XedniFixedFamilyRationalRootPlateau

private def offsets : List ℤ := [0, 1, 2, 3, 5, 8, 13, 21]
private def vectors : List (ℤ × ℤ) :=
  [(1, -6), (2, -1), (6, 5), (5, 4), (6, 1), (5, 3),
   (4, -5), (6, -1), (5, -1), (6, -5), (1, 5), (4, -1), (4, 1)]

private def instances : List ((ℤ × ℤ) × (ℤ × ℤ)) :=
  vectors.flatMap fun ab =>
    offsets.flatMap fun t₁ =>
      (offsets.filter (· ≠ t₁)).map fun t₂ => (ab, (t₁, t₂))

private def rationalRoot (e : (ℤ × ℤ) × (ℤ × ℤ)) : ℤ × ℤ := Id.run do
  let n := e.1.1 * e.2.1 + e.1.2 * e.2.2
  let d := e.1.1 + e.1.2
  let g : ℤ := Int.gcd n d
  let n' := n / g
  let d' := d / g
  if d' < 0 then return (-n', -d') else return (n', d')

def rationalRoots : List (ℤ × ℤ) :=
  (instances.map rationalRoot).eraseDups

/-- A nonzero integer whose absolute value is below the modulus remains
nonzero after reduction. -/
theorem cast_ne_zero_of_natAbs_lt (q : ℕ) [Fact (Nat.Prime q)]
    (n : ℤ) (hn : n ≠ 0) (hbound : n.natAbs < q) :
    (n : ZMod q) ≠ 0 := by
  intro hzero
  have hdvd : (q : ℤ) ∣ n :=
    (ZMod.intCast_zmod_eq_zero_iff_dvd n q).mp hzero
  have hle := Int.natAbs_le_of_dvd_ne_zero hdvd hn
  simp at hle
  omega

/-- Distinct integer fractions remain distinct modulo a prime larger than
their nonzero cross-determinant, provided both denominators survive. -/
theorem modular_roots_distinct_of_det_bound (q : ℕ) [Fact (Nat.Prime q)]
    (n d m e : ℤ)
    (hd : (d : ZMod q) ≠ 0) (he : (e : ZMod q) ≠ 0)
    (hdet : n * e - m * d ≠ 0)
    (hbound : (n * e - m * d).natAbs < q) :
    (n : ZMod q) / (d : ZMod q) ≠
      (m : ZMod q) / (e : ZMod q) := by
  intro hratio
  have hcross : (n : ZMod q) * (e : ZMod q) =
      (m : ZMod q) * (d : ZMod q) :=
    (div_eq_div_iff hd he).mp hratio
  have hzero : ((n * e - m * d : ℤ) : ZMod q) = 0 := by
    simpa only [Int.cast_sub, Int.cast_mul, sub_eq_zero] using hcross
  exact (cast_ne_zero_of_natAbs_lt q _ hdet hbound) hzero

private def modularRoot (q : ℕ) [Fact (Nat.Prime q)]
    (r : ℤ × ℤ) : ZMod q := (r.1 : ZMod q) / (r.2 : ZMod q)

/-- A finite certificate of bounded, pairwise nonzero cross-determinants
gives an injective modular root map. -/
theorem modular_root_image_card_of_certificate
    (q : ℕ) [Fact (Nat.Prime q)] (R : Finset (ℤ × ℤ))
    (hden : ∀ r ∈ R, r.2 ≠ 0 ∧ r.2.natAbs < q)
    (hdet : ∀ r ∈ R, ∀ s ∈ R, r ≠ s →
      r.1 * s.2 - s.1 * r.2 ≠ 0 ∧
        (r.1 * s.2 - s.1 * r.2).natAbs < q) :
    (R.image (modularRoot q)).card = R.card := by
  classical
  apply Finset.card_image_of_injOn
  intro r hr s hs heq
  by_contra hne
  obtain ⟨hdr, hdrBound⟩ := hden r hr
  obtain ⟨hds, hdsBound⟩ := hden s hs
  have hdrMod := cast_ne_zero_of_natAbs_lt q r.2 hdr hdrBound
  have hdsMod := cast_ne_zero_of_natAbs_lt q s.2 hds hdsBound
  obtain ⟨hdiff, hdiffBound⟩ := hdet r hr s hs hne
  exact (modular_roots_distinct_of_det_bound q r.1 r.2 s.1 s.2
    hdrMod hdsMod hdiff hdiffBound) heq

/-- If the certificate includes the rational zero root, the number of
nonzero modular roots is one less than its cardinality. -/
theorem modular_nonzero_root_image_card_of_certificate
    (q : ℕ) [Fact (Nat.Prime q)] (R : Finset (ℤ × ℤ))
    (hden : ∀ r ∈ R, r.2 ≠ 0 ∧ r.2.natAbs < q)
    (hdet : ∀ r ∈ R, ∀ s ∈ R, r ≠ s →
      r.1 * s.2 - s.1 * r.2 ≠ 0 ∧
        (r.1 * s.2 - s.1 * r.2).natAbs < q)
    (hzero : (0, 1) ∈ R) :
    ((R.image (modularRoot q)).erase 0).card = R.card - 1 := by
  classical
  have hz : (0 : ZMod q) ∈ R.image (modularRoot q) := by
    apply Finset.mem_image.mpr
    exact ⟨(0, 1), hzero, by simp [modularRoot]⟩
  rw [Finset.card_erase_of_mem hz]
  exact congrArg (· - 1) (modular_root_image_card_of_certificate q R hden hdet)

#print axioms cast_ne_zero_of_natAbs_lt
#print axioms modular_roots_distinct_of_det_bound
#print axioms modular_root_image_card_of_certificate
#print axioms modular_nonzero_root_image_card_of_certificate

end XedniFixedFamilyRationalRootPlateau
