import Mathlib.Tactic

/-! Canonical rational-root data for the frozen xedni coefficient and offset
family, with checked structural implications of a finite bound certificate. -/
namespace XedniFixedFamilyRationalRootPlateau

private def offsets : List ℤ := [0, 1, 2, 3, 5, 8, 13, 21]
private def vectors : List (ℤ × ℤ) :=
  [(1, -6), (2, -1), (6, 5), (5, 4), (6, 1), (5, 3),
   (4, -5), (6, -1), (5, -1), (6, -5), (1, 5), (4, -1), (4, 1)]

private def rationalRoot (e : (ℤ × ℤ) × (ℤ × ℤ)) : ℤ × ℤ := Id.run do
  let n := e.1.1 * e.2.1 + e.1.2 * e.2.2
  let d := e.1.1 + e.1.2
  let g : ℤ := Int.gcd n d
  let n' := n / g
  let d' := d / g
  if d' < 0 then return (-n', -d') else return (n', d')

private def normalizePair (n d : ℤ) : ℤ × ℤ := Id.run do
  let g : ℤ := Int.gcd n d
  let n' := n / g
  let d' := d / g
  if d' < 0 then return (-n', -d') else return (n', d')

/-- Dividing both integer coordinates by their gcd and adjusting their sign
preserves the fraction's cross-product. -/
private theorem normalizePair_cross (n d : ℤ) :
    n * (normalizePair n d).2 = (normalizePair n d).1 * d := by
  have hn : ((Int.gcd n d : ℕ) : ℤ) ∣ n := Int.gcd_dvd_left n d
  have hd : ((Int.gcd n d : ℕ) : ℤ) ∣ d := Int.gcd_dvd_right n d
  have hne : n / (Int.gcd n d : ℤ) * (Int.gcd n d : ℤ) = n :=
    Int.ediv_mul_cancel hn
  have hde : d / (Int.gcd n d : ℤ) * (Int.gcd n d : ℤ) = d :=
    Int.ediv_mul_cancel hd
  have hcross : n * (d / (Int.gcd n d : ℤ)) =
      (n / (Int.gcd n d : ℤ)) * d := by
    calc
      n * (d / (Int.gcd n d : ℤ)) =
          ((n / (Int.gcd n d : ℤ)) * (Int.gcd n d : ℤ)) *
            (d / (Int.gcd n d : ℤ)) := by rw [hne]
      _ = (n / (Int.gcd n d : ℤ)) *
            ((d / (Int.gcd n d : ℤ)) * (Int.gcd n d : ℤ)) := by ring
      _ = (n / (Int.gcd n d : ℤ)) * d := by rw [hde]
  simp only [normalizePair]
  split_ifs <;> simp_all

/-- Each raw coefficient-offset numerator and denominator have the same
cross-product as the canonical rational-root pair. -/
private theorem rationalRoot_cross (e : (ℤ × ℤ) × (ℤ × ℤ)) :
    (e.1.1 * e.2.1 + e.1.2 * e.2.2) * (rationalRoot e).2 =
      (rationalRoot e).1 * (e.1.1 + e.1.2) := by
  simpa only [rationalRoot, normalizePair] using
    normalizePair_cross (e.1.1 * e.2.1 + e.1.2 * e.2.2) (e.1.1 + e.1.2)

private def rootsFor (ab : ℤ × ℤ) : List (ℤ × ℤ) :=
  offsets.flatMap fun t₁ =>
    (offsets.filter (· ≠ t₁)).map fun t₂ => rationalRoot (ab, (t₁, t₂))

private def entriesFor (ab : ℤ × ℤ) : List ((ℤ × ℤ) × (ℤ × ℤ)) :=
  offsets.flatMap fun t₁ =>
    (offsets.filter (· ≠ t₁)).map fun t₂ => (ab, (t₁, t₂))

private def entries : List ((ℤ × ℤ) × (ℤ × ℤ)) :=
  vectors.flatMap entriesFor

private theorem entries_map_rationalRoot :
    entries.map rationalRoot = vectors.flatMap rootsFor := by
  unfold entries entriesFor rootsFor
  simp [List.map_flatMap, List.map_map, Function.comp_def]

private theorem entriesFor_first (ab : ℤ × ℤ)
    (e : (ℤ × ℤ) × (ℤ × ℤ)) (he : e ∈ entriesFor ab) : e.1 = ab := by
  simp only [entriesFor, List.mem_flatMap, List.mem_map] at he
  obtain ⟨t₁, _, t₂, _, rfl⟩ := he
  rfl

private theorem entries_first_mem_vectors (e : (ℤ × ℤ) × (ℤ × ℤ))
    (he : e ∈ entries) : e.1 ∈ vectors := by
  simp only [entries, List.mem_flatMap] at he
  obtain ⟨ab, hab, heab⟩ := he
  rw [entriesFor_first ab e heab]
  exact hab

private theorem vectors_sum_bound :
    ∀ ab ∈ vectors, 0 < (ab.1 + ab.2).natAbs ∧
      (ab.1 + ab.2).natAbs ≤ 11 := by
  decide

def rationalRoots : List (ℤ × ℤ) :=
  (vectors.flatMap rootsFor).eraseDups

private theorem rationalRoot_mem_rationalRoots
    (e : (ℤ × ℤ) × (ℤ × ℤ)) (he : e ∈ entries) :
    rationalRoot e ∈ rationalRoots := by
  have h : rationalRoot e ∈ entries.map rationalRoot :=
    List.mem_map.mpr ⟨e, he, rfl⟩
  rw [entries_map_rationalRoot] at h
  simpa only [rationalRoots, List.mem_eraseDups] using h

private theorem rootsFor_first :
    rootsFor (1, -6) = [(6, 5), (12, 5), (18, 5), (6, 1), (48, 5), (78, 5), (126, 5), (-1, 5), (11, 5), (17, 5), (29, 5), (47, 5), (77, 5), (25, 1), (-2, 5), (4, 5), (16, 5), (28, 5), (46, 5), (76, 5), (124, 5), (-3, 5), (3, 5), (9, 5), (27, 5), (9, 1), (15, 1), (123, 5), (-1, 1), (1, 5), (7, 5), (13, 5), (43, 5), (73, 5), (121, 5), (-8, 5), (-2, 5), (4, 5), (2, 1), (22, 5), (14, 1), (118, 5), (-13, 5), (-7, 5), (-1, 5), (1, 1), (17, 5), (7, 1), (113, 5), (-21, 5), (-3, 1), (-9, 5), (-3, 5), (9, 5), (27, 5), (57, 5)] := by decide

private theorem rootsFor_1 :
    rootsFor (2, -1) = [(-1, 1), (-2, 1), (-3, 1), (-5, 1), (-8, 1), (-13, 1), (-21, 1), (2, 1), (0, 1), (-1, 1), (-3, 1), (-6, 1), (-11, 1), (-19, 1), (4, 1), (3, 1), (1, 1), (-1, 1), (-4, 1), (-9, 1), (-17, 1), (6, 1), (5, 1), (4, 1), (1, 1), (-2, 1), (-7, 1), (-15, 1), (10, 1), (9, 1), (8, 1), (7, 1), (2, 1), (-3, 1), (-11, 1), (16, 1), (15, 1), (14, 1), (13, 1), (11, 1), (3, 1), (-5, 1), (26, 1), (25, 1), (24, 1), (23, 1), (21, 1), (18, 1), (5, 1), (42, 1), (41, 1), (40, 1), (39, 1), (37, 1), (34, 1), (29, 1)] := by decide

private theorem rootsFor_2 :
    rootsFor (6, 5) = [(5, 11), (10, 11), (15, 11), (25, 11), (40, 11), (65, 11), (105, 11), (6, 11), (16, 11), (21, 11), (31, 11), (46, 11), (71, 11), (111, 11), (12, 11), (17, 11), (27, 11), (37, 11), (52, 11), (7, 1), (117, 11), (18, 11), (23, 11), (28, 11), (43, 11), (58, 11), (83, 11), (123, 11), (30, 11), (35, 11), (40, 11), (45, 11), (70, 11), (95, 11), (135, 11), (48, 11), (53, 11), (58, 11), (63, 11), (73, 11), (113, 11), (153, 11), (78, 11), (83, 11), (8, 1), (93, 11), (103, 11), (118, 11), (183, 11), (126, 11), (131, 11), (136, 11), (141, 11), (151, 11), (166, 11), (191, 11)] := by decide

private theorem rootsFor_3 :
    rootsFor (5, 4) = [(4, 9), (8, 9), (4, 3), (20, 9), (32, 9), (52, 9), (28, 3), (5, 9), (13, 9), (17, 9), (25, 9), (37, 9), (19, 3), (89, 9), (10, 9), (14, 9), (22, 9), (10, 3), (14, 3), (62, 9), (94, 9), (5, 3), (19, 9), (23, 9), (35, 9), (47, 9), (67, 9), (11, 1), (25, 9), (29, 9), (11, 3), (37, 9), (19, 3), (77, 9), (109, 9), (40, 9), (44, 9), (16, 3), (52, 9), (20, 3), (92, 9), (124, 9), (65, 9), (23, 3), (73, 9), (77, 9), (85, 9), (97, 9), (149, 9), (35, 3), (109, 9), (113, 9), (13, 1), (125, 9), (137, 9), (157, 9)] := by decide

private theorem rootsFor_4 :
    rootsFor (6, 1) = [(1, 7), (2, 7), (3, 7), (5, 7), (8, 7), (13, 7), (3, 1), (6, 7), (8, 7), (9, 7), (11, 7), (2, 1), (19, 7), (27, 7), (12, 7), (13, 7), (15, 7), (17, 7), (20, 7), (25, 7), (33, 7), (18, 7), (19, 7), (20, 7), (23, 7), (26, 7), (31, 7), (39, 7), (30, 7), (31, 7), (32, 7), (33, 7), (38, 7), (43, 7), (51, 7), (48, 7), (7, 1), (50, 7), (51, 7), (53, 7), (61, 7), (69, 7), (78, 7), (79, 7), (80, 7), (81, 7), (83, 7), (86, 7), (99, 7), (18, 1), (127, 7), (128, 7), (129, 7), (131, 7), (134, 7), (139, 7)] := by decide

private theorem rootsFor_5 :
    rootsFor (5, 3) = [(3, 8), (3, 4), (9, 8), (15, 8), (3, 1), (39, 8), (63, 8), (5, 8), (11, 8), (7, 4), (5, 2), (29, 8), (11, 2), (17, 2), (5, 4), (13, 8), (19, 8), (25, 8), (17, 4), (49, 8), (73, 8), (15, 8), (9, 4), (21, 8), (15, 4), (39, 8), (27, 4), (39, 4), (25, 8), (7, 2), (31, 8), (17, 4), (49, 8), (8, 1), (11, 1), (5, 1), (43, 8), (23, 4), (49, 8), (55, 8), (79, 8), (103, 8), (65, 8), (17, 2), (71, 8), (37, 4), (10, 1), (89, 8), (16, 1), (105, 8), (27, 2), (111, 8), (57, 4), (15, 1), (129, 8), (18, 1)] := by decide

private theorem rootsFor_6 :
    rootsFor (4, -5) = [(5, 1), (10, 1), (15, 1), (25, 1), (40, 1), (65, 1), (105, 1), (-4, 1), (6, 1), (11, 1), (21, 1), (36, 1), (61, 1), (101, 1), (-8, 1), (-3, 1), (7, 1), (17, 1), (32, 1), (57, 1), (97, 1), (-12, 1), (-7, 1), (-2, 1), (13, 1), (28, 1), (53, 1), (93, 1), (-20, 1), (-15, 1), (-10, 1), (-5, 1), (20, 1), (45, 1), (85, 1), (-32, 1), (-27, 1), (-22, 1), (-17, 1), (-7, 1), (33, 1), (73, 1), (-52, 1), (-47, 1), (-42, 1), (-37, 1), (-27, 1), (-12, 1), (53, 1), (-84, 1), (-79, 1), (-74, 1), (-69, 1), (-59, 1), (-44, 1), (-19, 1)] := by decide

private theorem rootsFor_7 :
    rootsFor (6, -1) = [(-1, 5), (-2, 5), (-3, 5), (-1, 1), (-8, 5), (-13, 5), (-21, 5), (6, 5), (4, 5), (3, 5), (1, 5), (-2, 5), (-7, 5), (-3, 1), (12, 5), (11, 5), (9, 5), (7, 5), (4, 5), (-1, 5), (-9, 5), (18, 5), (17, 5), (16, 5), (13, 5), (2, 1), (1, 1), (-3, 5), (6, 1), (29, 5), (28, 5), (27, 5), (22, 5), (17, 5), (9, 5), (48, 5), (47, 5), (46, 5), (9, 1), (43, 5), (7, 1), (27, 5), (78, 5), (77, 5), (76, 5), (15, 1), (73, 5), (14, 1), (57, 5), (126, 5), (25, 1), (124, 5), (123, 5), (121, 5), (118, 5), (113, 5)] := by decide

private theorem rootsFor_8 :
    rootsFor (5, -1) = [(-1, 4), (-1, 2), (-3, 4), (-5, 4), (-2, 1), (-13, 4), (-21, 4), (5, 4), (3, 4), (1, 2), (0, 1), (-3, 4), (-2, 1), (-4, 1), (5, 2), (9, 4), (7, 4), (5, 4), (1, 2), (-3, 4), (-11, 4), (15, 4), (7, 2), (13, 4), (5, 2), (7, 4), (1, 2), (-3, 2), (25, 4), (6, 1), (23, 4), (11, 2), (17, 4), (3, 1), (1, 1), (10, 1), (39, 4), (19, 2), (37, 4), (35, 4), (27, 4), (19, 4), (65, 4), (16, 1), (63, 4), (31, 2), (15, 1), (57, 4), (11, 1), (105, 4), (26, 1), (103, 4), (51, 2), (25, 1), (97, 4), (23, 1)] := by decide

private theorem rootsFor_9 :
    rootsFor (6, -5) = [(-5, 1), (-10, 1), (-15, 1), (-25, 1), (-40, 1), (-65, 1), (-105, 1), (6, 1), (-4, 1), (-9, 1), (-19, 1), (-34, 1), (-59, 1), (-99, 1), (12, 1), (7, 1), (-3, 1), (-13, 1), (-28, 1), (-53, 1), (-93, 1), (18, 1), (13, 1), (8, 1), (-7, 1), (-22, 1), (-47, 1), (-87, 1), (30, 1), (25, 1), (20, 1), (15, 1), (-10, 1), (-35, 1), (-75, 1), (48, 1), (43, 1), (38, 1), (33, 1), (23, 1), (-17, 1), (-57, 1), (78, 1), (73, 1), (68, 1), (63, 1), (53, 1), (38, 1), (-27, 1), (126, 1), (121, 1), (116, 1), (111, 1), (101, 1), (86, 1), (61, 1)] := by decide

private theorem rootsFor_10 :
    rootsFor (1, 5) = [(5, 6), (5, 3), (5, 2), (25, 6), (20, 3), (65, 6), (35, 2), (1, 6), (11, 6), (8, 3), (13, 3), (41, 6), (11, 1), (53, 3), (1, 3), (7, 6), (17, 6), (9, 2), (7, 1), (67, 6), (107, 6), (1, 2), (4, 3), (13, 6), (14, 3), (43, 6), (34, 3), (18, 1), (5, 6), (5, 3), (5, 2), (10, 3), (15, 2), (35, 3), (55, 3), (4, 3), (13, 6), (3, 1), (23, 6), (11, 2), (73, 6), (113, 6), (13, 6), (3, 1), (23, 6), (14, 3), (19, 3), (53, 6), (59, 3), (7, 2), (13, 3), (31, 6), (6, 1), (23, 3), (61, 6), (43, 3)] := by decide

private theorem rootsFor_11 :
    rootsFor (4, -1) = [(-1, 3), (-2, 3), (-1, 1), (-5, 3), (-8, 3), (-13, 3), (-7, 1), (4, 3), (2, 3), (1, 3), (-1, 3), (-4, 3), (-3, 1), (-17, 3), (8, 3), (7, 3), (5, 3), (1, 1), (0, 1), (-5, 3), (-13, 3), (4, 1), (11, 3), (10, 3), (7, 3), (4, 3), (-1, 3), (-3, 1), (20, 3), (19, 3), (6, 1), (17, 3), (4, 1), (7, 3), (-1, 3), (32, 3), (31, 3), (10, 1), (29, 3), (9, 1), (19, 3), (11, 3), (52, 3), (17, 1), (50, 3), (49, 3), (47, 3), (44, 3), (31, 3), (28, 1), (83, 3), (82, 3), (27, 1), (79, 3), (76, 3), (71, 3)] := by decide

private theorem rootsFor_12 :
    rootsFor (4, 1) = [(1, 5), (2, 5), (3, 5), (1, 1), (8, 5), (13, 5), (21, 5), (4, 5), (6, 5), (7, 5), (9, 5), (12, 5), (17, 5), (5, 1), (8, 5), (9, 5), (11, 5), (13, 5), (16, 5), (21, 5), (29, 5), (12, 5), (13, 5), (14, 5), (17, 5), (4, 1), (5, 1), (33, 5), (4, 1), (21, 5), (22, 5), (23, 5), (28, 5), (33, 5), (41, 5), (32, 5), (33, 5), (34, 5), (7, 1), (37, 5), (9, 1), (53, 5), (52, 5), (53, 5), (54, 5), (11, 1), (57, 5), (12, 1), (73, 5), (84, 5), (17, 1), (86, 5), (87, 5), (89, 5), (92, 5), (97, 5)] := by decide

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

private def rawRoot (q : ℕ) [Fact (Nat.Prime q)]
    (e : (ℤ × ℤ) × (ℤ × ℤ)) : ZMod q :=
  ((e.1.1 * e.2.1 + e.1.2 * e.2.2 : ℤ) : ZMod q) /
    ((e.1.1 + e.1.2 : ℤ) : ZMod q)

/-- Gcd normalization preserves each public modular quotient whenever its
raw and canonical denominators survive modulo the prime. -/
theorem rawRoot_eq_modularRoot (q : ℕ) [Fact (Nat.Prime q)]
    (e : (ℤ × ℤ) × (ℤ × ℤ))
    (hd : ((e.1.1 + e.1.2 : ℤ) : ZMod q) ≠ 0)
    (hrd : (((rationalRoot e).2 : ℤ) : ZMod q) ≠ 0) :
    rawRoot q e = modularRoot q (rationalRoot e) := by
  apply (div_eq_div_iff hd hrd).mpr
  have hcross := rationalRoot_cross e
  simp only [← Int.cast_mul]
  exact congrArg (fun z : ℤ => (z : ZMod q)) hcross

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

private def canonicalRoots : List (ℤ × ℤ) :=
  [(6, 5), (12, 5), (18, 5), (6, 1), (48, 5), (78, 5), (126, 5), (-1, 5), (11, 5), (17, 5), (29, 5), (47, 5), (77, 5), (25, 1), (-2, 5), (4, 5), (16, 5), (28, 5), (46, 5), (76, 5), (124, 5), (-3, 5), (3, 5), (9, 5), (27, 5), (9, 1), (15, 1), (123, 5), (-1, 1), (1, 5), (7, 5), (13, 5), (43, 5), (73, 5), (121, 5), (-8, 5), (2, 1), (22, 5), (14, 1), (118, 5), (-13, 5), (-7, 5), (1, 1), (7, 1), (113, 5), (-21, 5), (-3, 1), (-9, 5), (57, 5), (-2, 1), (-5, 1), (-8, 1), (-13, 1), (-21, 1), (0, 1), (-6, 1), (-11, 1), (-19, 1), (4, 1), (3, 1), (-4, 1), (-9, 1), (-17, 1), (5, 1), (-7, 1), (-15, 1), (10, 1), (8, 1), (16, 1), (13, 1), (11, 1), (26, 1), (24, 1), (23, 1), (21, 1), (18, 1), (42, 1), (41, 1), (40, 1), (39, 1), (37, 1), (34, 1), (29, 1), (5, 11), (10, 11), (15, 11), (25, 11), (40, 11), (65, 11), (105, 11), (6, 11), (16, 11), (21, 11), (31, 11), (46, 11), (71, 11), (111, 11), (12, 11), (17, 11), (27, 11), (37, 11), (52, 11), (117, 11), (18, 11), (23, 11), (28, 11), (43, 11), (58, 11), (83, 11), (123, 11), (30, 11), (35, 11), (45, 11), (70, 11), (95, 11), (135, 11), (48, 11), (53, 11), (63, 11), (73, 11), (113, 11), (153, 11), (78, 11), (93, 11), (103, 11), (118, 11), (183, 11), (126, 11), (131, 11), (136, 11), (141, 11), (151, 11), (166, 11), (191, 11), (4, 9), (8, 9), (4, 3), (20, 9), (32, 9), (52, 9), (28, 3), (5, 9), (13, 9), (17, 9), (25, 9), (37, 9), (19, 3), (89, 9), (10, 9), (14, 9), (22, 9), (10, 3), (14, 3), (62, 9), (94, 9), (5, 3), (19, 9), (23, 9), (35, 9), (47, 9), (67, 9), (29, 9), (11, 3), (77, 9), (109, 9), (40, 9), (44, 9), (16, 3), (20, 3), (92, 9), (124, 9), (65, 9), (23, 3), (73, 9), (85, 9), (97, 9), (149, 9), (35, 3), (113, 9), (125, 9), (137, 9), (157, 9), (1, 7), (2, 7), (3, 7), (5, 7), (8, 7), (13, 7), (6, 7), (9, 7), (11, 7), (19, 7), (27, 7), (12, 7), (15, 7), (17, 7), (20, 7), (25, 7), (33, 7), (18, 7), (23, 7), (26, 7), (31, 7), (39, 7), (30, 7), (32, 7), (38, 7), (43, 7), (51, 7), (48, 7), (50, 7), (53, 7), (61, 7), (69, 7), (78, 7), (79, 7), (80, 7), (81, 7), (83, 7), (86, 7), (99, 7), (127, 7), (128, 7), (129, 7), (131, 7), (134, 7), (139, 7), (3, 8), (3, 4), (9, 8), (15, 8), (39, 8), (63, 8), (5, 8), (11, 8), (7, 4), (5, 2), (29, 8), (11, 2), (17, 2), (5, 4), (13, 8), (19, 8), (25, 8), (17, 4), (49, 8), (73, 8), (9, 4), (21, 8), (15, 4), (27, 4), (39, 4), (7, 2), (31, 8), (43, 8), (23, 4), (55, 8), (79, 8), (103, 8), (65, 8), (71, 8), (37, 4), (89, 8), (105, 8), (27, 2), (111, 8), (57, 4), (129, 8), (65, 1), (105, 1), (36, 1), (61, 1), (101, 1), (17, 1), (32, 1), (57, 1), (97, 1), (-12, 1), (28, 1), (53, 1), (93, 1), (-20, 1), (-10, 1), (20, 1), (45, 1), (85, 1), (-32, 1), (-27, 1), (-22, 1), (33, 1), (73, 1), (-52, 1), (-47, 1), (-42, 1), (-37, 1), (-84, 1), (-79, 1), (-74, 1), (-69, 1), (-59, 1), (-44, 1), (-1, 4), (-1, 2), (-3, 4), (-5, 4), (-13, 4), (-21, 4), (1, 2), (-11, 4), (13, 4), (-3, 2), (25, 4), (19, 2), (35, 4), (19, 4), (65, 4), (63, 4), (31, 2), (105, 4), (103, 4), (51, 2), (97, 4), (-25, 1), (-40, 1), (-65, 1), (-105, 1), (-34, 1), (-99, 1), (12, 1), (-28, 1), (-53, 1), (-93, 1), (-87, 1), (30, 1), (-35, 1), (-75, 1), (48, 1), (43, 1), (38, 1), (-57, 1), (78, 1), (68, 1), (63, 1), (126, 1), (121, 1), (116, 1), (111, 1), (86, 1), (5, 6), (25, 6), (65, 6), (35, 2), (1, 6), (11, 6), (8, 3), (13, 3), (41, 6), (53, 3), (1, 3), (7, 6), (17, 6), (9, 2), (67, 6), (107, 6), (13, 6), (43, 6), (34, 3), (15, 2), (55, 3), (23, 6), (73, 6), (113, 6), (53, 6), (59, 3), (31, 6), (61, 6), (43, 3), (-1, 3), (-2, 3), (-5, 3), (-8, 3), (-13, 3), (2, 3), (-4, 3), (-17, 3), (7, 3), (17, 3), (32, 3), (31, 3), (29, 3), (52, 3), (50, 3), (49, 3), (47, 3), (44, 3), (83, 3), (82, 3), (27, 1), (79, 3), (76, 3), (71, 3), (2, 5), (8, 5), (21, 5), (14, 5), (33, 5), (23, 5), (41, 5), (32, 5), (34, 5), (37, 5), (53, 5), (52, 5), (54, 5), (84, 5), (86, 5), (87, 5), (89, 5), (92, 5), (97, 5)]

set_option maxRecDepth 8192 in
/-- The generated roots equal the explicit first-occurrence certificate. -/
theorem rationalRoots_eq_certificate : rationalRoots = canonicalRoots := by
  unfold rationalRoots canonicalRoots
  simp only [vectors, List.flatMap_cons, List.flatMap_nil,
    rootsFor_first, rootsFor_1, rootsFor_2, rootsFor_3, rootsFor_4,
    rootsFor_5, rootsFor_6, rootsFor_7, rootsFor_8, rootsFor_9,
    rootsFor_10, rootsFor_11, rootsFor_12]
  decide

set_option maxRecDepth 8192 in
/-- Kernel-checked exact count of distinct rational roots. -/
theorem rationalRoots_card : rationalRoots.length = 420 := by
  rw [rationalRoots_eq_certificate]
  decide

set_option maxRecDepth 8192 in
/-- The certificate contains 419 nonzero rational roots. -/
theorem rationalRoots_nonzero_card :
    (rationalRoots.filter (· ≠ (0, 1))).length = 419 := by
  rw [rationalRoots_eq_certificate]
  decide

set_option maxRecDepth 8192 in
/-- Every canonical denominator is positive and at most eleven. -/
theorem rationalRoots_denominator_bound :
    ∀ r ∈ rationalRoots, 0 < r.2 ∧ r.2 ≤ 11 := by
  rw [rationalRoots_eq_certificate]
  decide

set_option maxRecDepth 8192 in
/-- Every canonical numerator has absolute value at most 191. -/
theorem rationalRoots_numerator_bound :
    ∀ r ∈ rationalRoots, r.1.natAbs ≤ 191 := by
  rw [rationalRoots_eq_certificate]
  decide

set_option maxRecDepth 8192 in
/-- Every pair in the certificate is reduced to coprime numerator and
denominator. -/
theorem rationalRoots_coprime :
    ∀ r ∈ rationalRoots, Nat.Coprime r.1.natAbs r.2.natAbs := by
  rw [rationalRoots_eq_certificate]
  decide

/-- Distinct canonical roots have a nonzero cross-determinant. -/
theorem rationalRoots_crossdet_ne :
    ∀ r ∈ rationalRoots, ∀ s ∈ rationalRoots, r ≠ s →
      r.1 * s.2 - s.1 * r.2 ≠ 0 := by
  intro r hr s hs hne hzero
  have hcross : r.1 * s.2 = s.1 * r.2 := sub_eq_zero.mp hzero
  have hdr := (rationalRoots_denominator_bound r hr).1
  have hds := (rationalRoots_denominator_bound s hs).1
  have hratio : (r.1 : ℚ) / r.2 = (s.1 : ℚ) / s.2 := by
    apply (div_eq_div_iff (by exact_mod_cast ne_of_gt hdr)
      (by exact_mod_cast ne_of_gt hds)).mpr
    exact_mod_cast hcross
  obtain ⟨hn, hd⟩ := Rat.div_int_inj hdr hds
    (rationalRoots_coprime r hr) (rationalRoots_coprime s hs) hratio
  exact hne (Prod.ext hn hd)

/-- The checked coordinate bounds give a uniform determinant bound. -/
theorem rationalRoots_crossdet_bound_4202 :
    ∀ r ∈ rationalRoots, ∀ s ∈ rationalRoots,
      (r.1 * s.2 - s.1 * r.2).natAbs ≤ 4202 := by
  intro r hr s hs
  have hrn : |r.1| ≤ (191 : ℤ) := by
    have h : ((r.1.natAbs : ℕ) : ℤ) ≤ 191 := by
      exact_mod_cast rationalRoots_numerator_bound r hr
    simpa only [Int.natCast_natAbs] using h
  have hsn : |s.1| ≤ (191 : ℤ) := by
    have h : ((s.1.natAbs : ℕ) : ℤ) ≤ 191 := by
      exact_mod_cast rationalRoots_numerator_bound s hs
    simpa only [Int.natCast_natAbs] using h
  have hrd : |r.2| ≤ (11 : ℤ) := by
    rw [abs_of_pos (rationalRoots_denominator_bound r hr).1]
    exact (rationalRoots_denominator_bound r hr).2
  have hsd : |s.2| ≤ (11 : ℤ) := by
    rw [abs_of_pos (rationalRoots_denominator_bound s hs).1]
    exact (rationalRoots_denominator_bound s hs).2
  have hbound : |r.1 * s.2 - s.1 * r.2| ≤ (4202 : ℤ) := by
    calc
      _ ≤ |r.1 * s.2| + |s.1 * r.2| := by
        simpa [sub_eq_add_neg] using
          (abs_add_le (r.1 * s.2) (-(s.1 * r.2)))
      _ = |r.1| * |s.2| + |s.1| * |r.2| := by rw [abs_mul, abs_mul]
      _ ≤ 191 * 11 + 191 * 11 := by gcongr
      _ = 4202 := by norm_num
  have hnat : (((r.1 * s.2 - s.1 * r.2).natAbs : ℕ) : ℤ) ≤ 4202 := by
    simpa only [Int.natCast_natAbs] using hbound
  exact_mod_cast hnat

set_option maxRecDepth 8192 in
set_option maxHeartbeats 0 in
/-- The certified canonical roots have 419 distinct nonzero images for every
prime above the checked coordinate-bound threshold. -/
theorem canonical_modular_roots_card_419
    (q : ℕ) [Fact (Nat.Prime q)] (hq : 4202 < q) :
    (((rationalRoots.toFinset).image (modularRoot q)).erase 0).card = 419 := by
  classical
  let R : Finset (ℤ × ℤ) := rationalRoots.toFinset
  have hnodup : rationalRoots.Nodup := by
    rw [rationalRoots_eq_certificate]
    decide
  have hRcard : R.card = 420 := by
    change rationalRoots.toFinset.card = 420
    rw [List.toFinset_card_of_nodup hnodup]
    exact rationalRoots_card
  have hden : ∀ r ∈ R, r.2 ≠ 0 ∧ r.2.natAbs < q := by
    intro r hr
    have hrList : r ∈ rationalRoots := by simpa [R] using hr
    obtain ⟨hpos, hle⟩ := rationalRoots_denominator_bound r hrList
    constructor
    · exact ne_of_gt hpos
    · have hnat : r.2.natAbs ≤ 11 := by
        omega
      omega
  have hdet : ∀ r ∈ R, ∀ s ∈ R, r ≠ s →
      r.1 * s.2 - s.1 * r.2 ≠ 0 ∧
        (r.1 * s.2 - s.1 * r.2).natAbs < q := by
    intro r hr s hs hne
    have hrList : r ∈ rationalRoots := by simpa [R] using hr
    have hsList : s ∈ rationalRoots := by simpa [R] using hs
    exact ⟨rationalRoots_crossdet_ne r hrList s hsList hne,
      lt_of_le_of_lt (rationalRoots_crossdet_bound_4202 r hrList s hsList) hq⟩
  have hzero : (0, 1) ∈ R := by
    change (0, 1) ∈ rationalRoots.toFinset
    rw [List.mem_toFinset, rationalRoots_eq_certificate]
    decide
  have h := modular_nonzero_root_image_card_of_certificate q R hden hdet hzero
  simpa [R, hRcard] using h

/-- Every frozen coefficient-offset quotient equals its canonical modular
fraction above the denominator bound. -/
theorem frozen_rawRoot_eq_modularRoot
    (q : ℕ) [Fact (Nat.Prime q)] (hq : 4202 < q)
    (e : (ℤ × ℤ) × (ℤ × ℤ)) (he : e ∈ entries) :
    rawRoot q e = modularRoot q (rationalRoot e) := by
  have hv := vectors_sum_bound e.1 (entries_first_mem_vectors e he)
  have hd0 : e.1.1 + e.1.2 ≠ 0 := by
    intro hz
    simp [hz] at hv
  have hdBound : (e.1.1 + e.1.2).natAbs < q := by omega
  have hd := cast_ne_zero_of_natAbs_lt q _ hd0 hdBound
  have hr := rationalRoots_denominator_bound (rationalRoot e)
    (rationalRoot_mem_rationalRoots e he)
  have hrd0 : (rationalRoot e).2 ≠ 0 := ne_of_gt hr.1
  have hrdBound : (rationalRoot e).2.natAbs < q := by omega
  have hrd := cast_ne_zero_of_natAbs_lt q _ hrd0 hrdBound
  exact rawRoot_eq_modularRoot q e hd hrd

/-- The raw public equations of the frozen family have exactly 419 distinct
nonzero roots for every prime above the checked determinant threshold. -/
theorem frozen_raw_roots_card_419
    (q : ℕ) [Fact (Nat.Prime q)] (hq : 4202 < q) :
    (((entries.toFinset).image (rawRoot q)).erase 0).card = 419 := by
  classical
  have hmap : entries.toFinset.image rationalRoot = rationalRoots.toFinset := by
    ext r
    simp only [Finset.mem_image, List.mem_toFinset]
    constructor
    · rintro ⟨e, he, rfl⟩
      exact rationalRoot_mem_rationalRoots e he
    · intro hr
      have h : r ∈ entries.map rationalRoot := by
        rw [entries_map_rationalRoot]
        simpa only [rationalRoots, List.mem_eraseDups] using hr
      obtain ⟨e, he, rfl⟩ := List.mem_map.mp h
      exact ⟨e, he, rfl⟩
  have hraw : entries.toFinset.image (rawRoot q) =
      entries.toFinset.image (fun e => modularRoot q (rationalRoot e)) := by
    apply Finset.image_congr
    intro e he
    exact frozen_rawRoot_eq_modularRoot q hq e (by simpa using he)
  have hcomp : entries.toFinset.image (fun e => modularRoot q (rationalRoot e)) =
      (entries.toFinset.image rationalRoot).image (modularRoot q) := by
    rw [Finset.image_image]
    rfl
  rw [hraw, hcomp, hmap]
  exact canonical_modular_roots_card_419 q hq

#print axioms rationalRoots_card
#print axioms rationalRoots_eq_certificate
#print axioms rationalRoots_nonzero_card
#print axioms rationalRoots_denominator_bound
#print axioms rationalRoots_numerator_bound
#print axioms rationalRoots_coprime
#print axioms rationalRoots_crossdet_ne
#print axioms rationalRoots_crossdet_bound_4202
#print axioms cast_ne_zero_of_natAbs_lt
#print axioms modular_roots_distinct_of_det_bound
#print axioms modular_root_image_card_of_certificate
#print axioms modular_nonzero_root_image_card_of_certificate
#print axioms canonical_modular_roots_card_419
#print axioms rawRoot_eq_modularRoot
#print axioms frozen_rawRoot_eq_modularRoot
#print axioms frozen_raw_roots_card_419

end XedniFixedFamilyRationalRootPlateau
