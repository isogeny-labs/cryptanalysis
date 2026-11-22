import HandbookIC.Core

/-!
# HandbookIC.Ideas.B07 — handbook ideas H061 .. H070
(relation filtering H061-H063, linear algebra H064-H067, descent H068-H070)

Each idea has a doc comment, definitions prefixed by the lower-case id,
`def Hxxx_claim : Prop` (hypotheses explicit, nothing postulated) and at least
one proved supporting theorem.  Empirical rates are never proved here.
-/

namespace HandbookIC.Ideas.B07

open HandbookIC

/-! ## Shared counting helpers -/

/-- Pigeonhole: a duplicate-free list contained in another is no longer. -/
theorem b07_nodup_le {α : Type} (l1 l2 : List α) (hn : l1.Nodup) (hs : l1 ⊆ l2) :
    l1.length ≤ l2.length :=
  hn.length_le_of_subset hs

/-- If every target below `N` occurs in `l`, then `N ≤ l.length`. -/
theorem b07_cover_le (N : Nat) (l : List Nat) (h : ∀ t, t < N → t ∈ l) :
    N ≤ l.length := by
  have hs : (List.range N) ⊆ l := fun t ht => h t (List.mem_range.mp ht)
  have := b07_nodup_le _ _ (List.nodup_range) hs
  simpa using this

/-- Length of a `flatMap` whose pieces all have the same length `c`. -/
theorem b07_flatMap_length {α β : Type} (l : List α) (f : α → List β) (c : Nat)
    (h : ∀ x, (f x).length = c) : (l.flatMap f).length = l.length * c := by
  induction l with
  | nil => simp
  | cons x xs ih =>
    simp only [List.flatMap_cons, List.length_append, List.length_cons, ih, h]
    rw [Nat.succ_mul]; omega

/-! ## H061 -/

/-- **H061** — Z/4 torsion character from halving to prune sign patterns and
reject corrupt rows.  Handbook 12.2.6, 12.2.7.  Phase: relation-filtering.
Claim: on a cofactor-4 curve a homomorphism `psi4 : E → Z/4` turns every valid
signed relation into `Σ ε_i psi4(P_i) ≡ psi4(R) (mod 4)`; when all `psi4(P_i)`
are odd exactly `2^(m-1)` of the `2^m` sign patterns survive. -/
structure h061Hom (G : Type) where
  add : G → G → G
  neg : G → G
  psi : G → Int
  psi_add : ∀ x y, psi (add x y) % 4 = (psi x + psi y) % 4
  psi_neg : ∀ x, psi (neg x) % 4 = (- psi x) % 4

/-- Signed point `ε·P`. -/
def h061Signed {G : Type} (H : h061Hom G) (e : Bool) (P : G) : G :=
  if e then P else H.neg P

/-- Group sum of a signed list. -/
def h061Sum {G : Type} (H : h061Hom G) (zero : G) : List (Bool × G) → G
  | [] => zero
  | (e, P) :: t => H.add (h061Signed H e P) (h061Sum H zero t)

/-- The character side `Σ ε_i psi4(P_i)`. -/
def h061Char {G : Type} (H : h061Hom G) : List (Bool × G) → Int
  | [] => 0
  | (e, P) :: t => (if e then H.psi P else - H.psi P) + h061Char H t

/-- All sign patterns of length `m`. -/
def h061Patterns : Nat → List (List Bool)
  | 0 => [[]]
  | m + 1 => (h061Patterns m).flatMap (fun s => [true :: s, false :: s])

/-- Signed sum of integer characters `ps` under sign pattern `es`. -/
def h061Val (ps : List Int) (es : List Bool) : Int :=
  ((ps.zip es).map (fun pe => if pe.2 then pe.1 else - pe.1)).sum

/-- Number of surviving patterns for target character `r`. -/
def h061Survivors (ps : List Int) (r : Int) : Nat :=
  ((h061Patterns ps.length).filter (fun es => h061Val ps es % 4 == r % 4)).length

def H061_claim : Prop :=
  (∀ (G : Type) (H : h061Hom G) (zero : G), H.psi zero % 4 = 0 →
    ∀ (l : List (Bool × G)) (R : G), R = h061Sum H zero l →
      H.psi R % 4 = h061Char H l % 4) ∧
  (∀ (ps : List Int) (r : Int), 0 < ps.length → (∀ p ∈ ps, p % 2 = 1) →
    r % 2 = (ps.length : Int) % 2 →
    h061Survivors ps r = 2 ^ (ps.length - 1))

theorem H061_relation_character {G : Type} (H : h061Hom G) (zero : G)
    (hz : H.psi zero % 4 = 0) (l : List (Bool × G)) :
    H.psi (h061Sum H zero l) % 4 = h061Char H l % 4 := by
  induction l with
  | nil => simp [h061Sum, h061Char, hz]
  | cons ep t ih =>
    obtain ⟨e, P⟩ := ep
    have h1 := H.psi_add (h061Signed H e P) (h061Sum H zero t)
    have h2 : H.psi (h061Signed H e P) % 4
        = (if e then H.psi P else - H.psi P) % 4 := by
      cases e
      · simp [h061Signed, H.psi_neg]
      · simp [h061Signed]
    simp only [h061Sum, h061Char]
    omega

theorem H061_patterns_length (m : Nat) : (h061Patterns m).length = 2 ^ m := by
  induction m with
  | zero => simp [h061Patterns]
  | succ m ih =>
    unfold h061Patterns
    rw [b07_flatMap_length _ _ 2 (fun _ => rfl), ih, Nat.pow_succ]

theorem H061_survivors_m3 : h061Survivors [1, 1, 1] 3 = 4 := by decide

theorem H061_survivors_m4 : h061Survivors [1, 3, 1, 3] 0 = 8 := by decide

theorem H061_survivors_half_m3 :
    h061Survivors [1, 1, 1] 3 * 2 = (h061Patterns 3).length := by
  rw [H061_patterns_length]; decide

/-! ## H062 -/

/-- **H062** — Coupon-collector relation count and orbit-quotient coverage.
Handbook 11.6.10, 11.2.3.5.  Phase: relation-filtering.  Claim: relations with
at most `m` columns each cover all `B` columns only if there are at least
`B/m` of them; a surjective fold to `B/k` orbit columns gives `(B/k)/m`. -/
def h062Covers (B : Nat) (rels : List (List Nat)) : Prop :=
  ∀ i, i < B → ∃ s ∈ rels, i ∈ s

theorem H062_flatten_len (m : Nat) (rels : List (List Nat))
    (h : ∀ s ∈ rels, s.length ≤ m) : rels.flatten.length ≤ m * rels.length := by
  induction rels with
  | nil => simp
  | cons s t ih =>
    have h1 := h s (List.mem_cons_self)
    have h2 := ih (fun u hu => h u (List.mem_cons_of_mem _ hu))
    simp only [List.flatten_cons, List.length_append, List.length_cons]
    rw [Nat.mul_succ]; omega

theorem H062_cover_bound (B m : Nat) (rels : List (List Nat))
    (hm : ∀ s ∈ rels, s.length ≤ m) (hc : h062Covers B rels) :
    B ≤ m * rels.length := by
  have hsub : ∀ i, i < B → i ∈ rels.flatten := by
    intro i hi
    obtain ⟨s, hs, hi'⟩ := hc i hi
    exact List.mem_flatten.mpr ⟨s, hs, hi'⟩
  have := b07_cover_le B rels.flatten hsub
  have := H062_flatten_len m rels hm
  omega

theorem H062_orbit_cover_bound (B k m : Nat) (rels : List (List Nat))
    (hm : ∀ s ∈ rels, s.length ≤ m)
    (hc : h062Covers (orbitRepresentatives B k) rels) :
    orbitRepresentatives B k ≤ m * rels.length ∧ orbitRepresentatives B k ≤ B :=
  ⟨H062_cover_bound _ m rels hm hc, orbitRepresentatives_le B k⟩

def H062_claim : Prop :=
  ∀ (B k m : Nat) (rels : List (List Nat)), (∀ s ∈ rels, s.length ≤ m) →
    (h062Covers B rels → B ≤ m * rels.length) ∧
    (h062Covers (orbitRepresentatives B k) rels →
      orbitRepresentatives B k ≤ m * rels.length)

theorem H062_claim_holds : H062_claim := fun B k m rels hm =>
  ⟨H062_cover_bound B m rels hm, H062_cover_bound _ m rels hm⟩

/-! ## H063 -/

/-- **H063** — Run-structure canonicalisation of normal-basis necklaces.
Handbook 10.2.4, 10.3.2.  Phase: relation-filtering.  Claim: the
lexicographically minimal rotation of a bit vector has a maximal leading run
of zeros among all rotations, so only rotations starting at a maximal zero
run are candidates. -/
def h063Rot (v : List Bool) (k : Nat) : List Bool := v.drop k ++ v.take k

/-- Lexicographic order, `false < true`. -/
def h063LexLe : List Bool → List Bool → Bool
  | [], _ => true
  | _ :: _, [] => false
  | a :: as, b :: bs => if a == b then h063LexLe as bs else (a == false)

/-- Length of the leading run of zeros. -/
def h063Lz : List Bool → Nat
  | [] => 0
  | true :: _ => 0
  | false :: t => h063Lz t + 1

theorem H063_rot_length (v : List Bool) (k : Nat) : (h063Rot v k).length = v.length := by
  simp only [h063Rot, List.length_append, List.length_drop, List.length_take]
  omega

theorem H063_lexLe_lz : ∀ (a b : List Bool), a.length = b.length →
    h063LexLe a b = true → h063Lz b ≤ h063Lz a
  | [], [], _, _ => by simp [h063Lz]
  | [], _ :: _, h, _ => by simp at h
  | _ :: _, [], h, _ => by simp at h
  | x :: as, y :: bs, h, hl => by
    have h' : as.length = bs.length := by simpa using h
    cases x <;> cases y
    · have := H063_lexLe_lz as bs h' (by simpa [h063LexLe] using hl)
      simp [h063Lz]; omega
    · simp [h063Lz]
    · simp [h063LexLe] at hl
    · simp [h063Lz]

def H063_claim : Prop :=
  ∀ (v : List Bool) (k0 : Nat),
    (∀ k, h063LexLe (h063Rot v k0) (h063Rot v k) = true) →
    ∀ k, h063Lz (h063Rot v k) ≤ h063Lz (h063Rot v k0)

theorem H063_claim_holds : H063_claim := by
  intro v k0 hmin k
  exact H063_lexLe_lz _ _ (by rw [H063_rot_length, H063_rot_length]) (hmin k)

theorem H063_instance :
    ((List.range 6).all (fun k =>
      h063LexLe (h063Rot [true, false, false, true, false, true] 1)
        (h063Rot [true, false, false, true, false, true] k))) = true := by decide

/-! ## H064 -/

/-- **H064** — Sparse fountain-coded SpMV for block Wiedemann on Spot.
Handbook 17.3.8.  Phase: linear-algebra.  Claim: when the received coded
results determine the products linearly (decoder `dec` inverts encoder `enc`),
`A v` is a function of the received results; the coded flop factor `f/100`
below 2 beats replication in core-seconds. -/
def h064CodedCost (work f100 : Nat) : Nat := work * f100 / 100

/-- 2 data blocks plus 1 parity block. -/
def h064Enc (y0 y1 : Int) : Fin 3 → Int
  | 0 => y0
  | 1 => y1
  | 2 => y0 + y1

def H064_claim : Prop :=
  (∀ {k r : Nat} (enc : (Fin k → Int) → (Fin r → Int))
      (dec : (Fin r → Int) → (Fin k → Int)),
    (∀ y, dec (enc y) = y) → ∀ y, dec (enc y) = y) ∧
  (∀ work f100 : Nat, 0 < work → f100 < 200 →
    h064CodedCost work f100 < 2 * work)

theorem H064_cost_lt_replication (work f100 : Nat) (hw : 0 < work) (hf : f100 < 200) :
    h064CodedCost work f100 < 2 * work := by
  unfold h064CodedCost
  have : work * f100 < work * 200 := Nat.mul_lt_mul_of_pos_left hf hw
  omega

theorem H064_decode_any_two (y0 y1 : Int) :
    (h064Enc y0 y1 1 = y1 ∧ h064Enc y0 y1 2 - h064Enc y0 y1 1 = y0) ∧
    (h064Enc y0 y1 0 = y0 ∧ h064Enc y0 y1 2 - h064Enc y0 y1 0 = y1) ∧
    (h064Enc y0 y1 0 = y0 ∧ h064Enc y0 y1 1 = y1) := by
  simp [h064Enc]
  omega

theorem H064_claim_holds : H064_claim :=
  ⟨fun _ _ h => h, H064_cost_lt_replication⟩

/-! ## H065 -/

/-- **H065** — Block Wiedemann early stop by confirmed linear-complexity profile.
Handbook 17.2.4, 17.3.1.  Phase: linear-algebra.  Claim: the linear complexity
of a prefix is monotone in the prefix length and at most `N`; stopping at
`2L + δ` saves SpMVs when `L` is 3% below the a-priori bound `M`. -/
def h065First (p : Nat → Bool) : Nat → Nat → Nat
  | 0, L => L
  | fuel + 1, L => if p L then L else h065First p fuel (L + 1)

/-- Least `L ≤ N` with `ok t L` (fallback `N`), `ok t L` = a recurrence of order
`L` explains the first `t` terms. -/
def h065LinComp (ok : Nat → Nat → Bool) (t N : Nat) : Nat := h065First (ok t) N 0

theorem H065_first_ge (p : Nat → Bool) : ∀ fuel L, L ≤ h065First p fuel L
  | 0, L => by simp [h065First]
  | fuel + 1, L => by
    unfold h065First
    split
    · exact Nat.le_refl _
    · have := H065_first_ge p fuel (L + 1); omega

theorem H065_first_le (p : Nat → Bool) : ∀ fuel L, h065First p fuel L ≤ L + fuel
  | 0, L => by simp [h065First]
  | fuel + 1, L => by
    unfold h065First
    split
    · omega
    · have := H065_first_le p fuel (L + 1); omega

theorem H065_first_mono (p p' : Nat → Bool) (h : ∀ L, p' L = true → p L = true) :
    ∀ fuel L, h065First p fuel L ≤ h065First p' fuel L
  | 0, L => by simp [h065First]
  | fuel + 1, L => by
    unfold h065First
    by_cases h1 : p' L = true
    · have h2 := h L h1
      simp [h1, h2]
    · have h1' : p' L = false := by simpa using h1
      by_cases h2 : p L = true
      · simp [h1', h2]
        exact H065_first_ge p' fuel (L + 1) |> fun x => by omega
      · have h2' : p L = false := by simpa using h2
        simp [h1', h2']
        exact H065_first_mono p p' h fuel (L + 1)

theorem H065_linComp_mono (ok : Nat → Nat → Bool) (N : Nat)
    (hmono : ∀ t t' L, t ≤ t' → ok t' L = true → ok t L = true) :
    ∀ t t', t ≤ t' → h065LinComp ok t N ≤ h065LinComp ok t' N := by
  intro t t' htt
  exact H065_first_mono _ _ (fun L hL => hmono t t' L htt hL) N 0

theorem H065_linComp_le (ok : Nat → Nat → Bool) (t N : Nat) :
    h065LinComp ok t N ≤ N := by
  have := H065_first_le (ok t) N 0
  unfold h065LinComp; omega

theorem H065_saving (L M δ : Nat) (hL : 100 * L ≤ 97 * M) (hδ : 50 * δ ≤ M) :
    100 * (2 * L + δ) ≤ 98 * (2 * M) := by omega

def H065_claim : Prop :=
  ∀ (ok : Nat → Nat → Bool) (N : Nat),
    (∀ t t' L, t ≤ t' → ok t' L = true → ok t L = true) →
    (∀ t t', t ≤ t' → h065LinComp ok t N ≤ h065LinComp ok t' N) ∧
    (∀ t, h065LinComp ok t N ≤ N) ∧
    (∀ L M δ : Nat, 100 * L ≤ 97 * M → 50 * δ ≤ M →
      100 * (2 * L + δ) ≤ 98 * (2 * M))

theorem H065_claim_holds : H065_claim := fun ok N hm =>
  ⟨H065_linComp_mono ok N hm, fun t => H065_linComp_le ok t N, H065_saving⟩

/-! ## H066 -/

/-- **H066** — Functional-only Wiedemann reading kernel coordinates from the BM
sequence.  Handbook 16.2.1.  Phase: linear-algebra.  Claim: for a linear
functional `u` and `x = Σ c_k v_k`, `u(x) = Σ c_k u(v_k)`, so one coordinate of
`x` is read off from scalar sequence values; the matvec count drops from `3N`
to `2N + c`. -/
def h066Vsum (d : Nat) : (B : Nat) → (Fin B → Fin d → Int) → Fin d → Int
  | 0, _ => fun _ => 0
  | B + 1, f => fun i => h066Vsum d B (fun k => f k.castSucc) i + f (Fin.last B) i

/-- `u` is a linear functional. -/
structure h066Linear (d : Nat) (u : (Fin d → Int) → Int) : Prop where
  add : ∀ x y, u (fun i => x i + y i) = u x + u y
  smul : ∀ (c : Int) x, u (fun i => c * x i) = c * u x

theorem H066_functional_comb {d : Nat} (u : (Fin d → Int) → Int)
    (hu : h066Linear d u) : ∀ (B : Nat) (c : Fin B → Int) (v : Fin B → Fin d → Int),
    u (h066Vsum d B (fun k i => c k * v k i)) = finSum B (fun k => c k * u (v k))
  | 0, c, v => by
    have h0 := hu.smul 0 (fun _ => (0 : Int))
    simp only [Int.zero_mul] at h0
    simp [h066Vsum, finSum]
    omega
  | B + 1, c, v => by
    have ih := H066_functional_comb u hu B (fun k => c k.castSucc) (fun k => v k.castSucc)
    have h := hu.add (h066Vsum d B (fun k i => c k.castSucc * v k.castSucc i))
      (fun i => c (Fin.last B) * v (Fin.last B) i)
    have h' := hu.smul (c (Fin.last B)) (v (Fin.last B))
    simp only [h066Vsum, finSum]
    rw [h, ih, h']

theorem H066_matvec_count (N c : Nat) (hc : 100 * c ≤ N) :
    3 * N - N = 2 * N ∧ 100 * (2 * N + c) ≤ 67 * (3 * N) := by omega

def H066_claim : Prop :=
  ∀ (d : Nat) (u : (Fin d → Int) → Int), h066Linear d u →
    ∀ (B : Nat) (c : Fin B → Int) (v : Fin B → Fin d → Int),
      u (h066Vsum d B (fun k i => c k * v k i)) = finSum B (fun k => c k * u (v k))

theorem H066_claim_holds : H066_claim := fun d u hu B c v =>
  H066_functional_comb u hu B c v

/-! ## H067 -/

/-- **H067** — Displacement-rank solve of the un-quotiented Frobenius-twisted
relation matrix.  Handbook 13.4.5.2, 13.2.6.  Phase: linear-algebra.  Claim:
if the matrix `M` is shift-invariant (`M i j = M (i+1) (j+1)`) away from a list
of orbit boundaries, then the number of rows of the displacement `M - Z M Zᵀ`
that are non-zero is at most the number of boundaries (a bound on the
displacement rank). -/
def h067NonzeroRow (M : Nat → Nat → Int) (ncols : Nat) (i : Nat) : Bool :=
  (List.range ncols).any (fun j => M i j != M (i + 1) (j + 1))

def h067Count (M : Nat → Nat → Int) (B ncols : Nat) : Nat :=
  ((List.range B).filter (h067NonzeroRow M ncols)).length

theorem H067_count_le (M : Nat → Nat → Int) (B ncols : Nat) (bd : List Nat)
    (hshift : ∀ i, i ∉ bd → ∀ j, j < ncols → M i j = M (i + 1) (j + 1)) :
    h067Count M B ncols ≤ bd.length := by
  unfold h067Count
  apply b07_nodup_le _ _ ((List.nodup_range).filter _)
  intro i hi
  rw [List.mem_filter] at hi
  by_cases hb : i ∈ bd
  · exact hb
  · exfalso
    have h2 := hi.2
    simp only [h067NonzeroRow, List.any_eq_true, List.mem_range, bne_iff_ne, ne_eq] at h2
    obtain ⟨j, hj, hne⟩ := h2
    exact hne (hshift i hb j hj)

def H067_claim : Prop :=
  ∀ (M : Nat → Nat → Int) (B ncols : Nat) (bd : List Nat),
    (∀ i, i ∉ bd → ∀ j, j < ncols → M i j = M (i + 1) (j + 1)) →
    h067Count M B ncols ≤ bd.length

theorem H067_claim_holds : H067_claim := H067_count_le

theorem H067_instance :
    h067Count (fun i j => if i = j then 1 else 0) 6 6 = 0 := by decide

/-! ## H068 -/

/-- **H068** — Waring-type coverage threshold for descent steps.
Handbook 13.1.6.  Phase: descent.  Claim: if every target `t < 2^n` is a sum of
`k` elements of a set `V` with `2^m` elements, then `n ≤ k·m` (necessary
condition `km ≥ n`). -/
def h068Tuples {α : Type} (V : List α) : Nat → List (List α)
  | 0 => [[]]
  | k + 1 => V.flatMap (fun v => (h068Tuples V k).map (v :: ·))

theorem H068_tuples_length {α : Type} (V : List α) (k : Nat) :
    (h068Tuples V k).length = V.length ^ k := by
  induction k with
  | zero => simp [h068Tuples]
  | succ k ih =>
    unfold h068Tuples
    rw [b07_flatMap_length _ _ (V.length ^ k) (fun _ => by simp [ih]), Nat.pow_succ,
      Nat.mul_comm]

theorem H068_cover_count {α : Type} (V : List α) (k N : Nat) (sumF : List α → Nat)
    (h : ∀ t, t < N → ∃ s ∈ h068Tuples V k, sumF s = t) : N ≤ V.length ^ k := by
  have hc : ∀ t, t < N → t ∈ (h068Tuples V k).map sumF := by
    intro t ht
    obtain ⟨s, hs, hst⟩ := h t ht
    exact List.mem_map.mpr ⟨s, hs, hst⟩
  have := b07_cover_le N _ hc
  simpa [H068_tuples_length] using this

theorem H068_necessary {α : Type} (V : List α) (n m k : Nat) (sumF : List α → Nat)
    (hV : V.length = 2 ^ m)
    (h : ∀ t, t < 2 ^ n → ∃ s ∈ h068Tuples V k, sumF s = t) : n ≤ m * k := by
  have h1 := H068_cover_count V k (2 ^ n) sumF h
  rw [hV, ← Nat.pow_mul] at h1
  exact (Nat.pow_le_pow_iff_right (by omega)).mp h1

def H068_claim : Prop :=
  ∀ {α : Type} (V : List α) (n m k : Nat) (sumF : List α → Nat),
    V.length = 2 ^ m →
    (∀ t, t < 2 ^ n → ∃ s ∈ h068Tuples V k, sumF s = t) → n ≤ m * k

theorem H068_claim_holds : H068_claim := fun V n m k sumF hV h =>
  H068_necessary V n m k sumF hV h

/-! ## H069 -/

/-- **H069** — Riemann-Roch counting threshold on descent level size.
Handbook 12.1.2.  Phase: descent.  Claim: if every target `t < N` is the
`sumF` of some `(m-1)`-subset of `V'`, then `N ≤ C(|V'|, m-1)`. -/
def h069Choose : Nat → Nat → Nat
  | _, 0 => 1
  | 0, _ + 1 => 0
  | n + 1, k + 1 => h069Choose n k + h069Choose n (k + 1)

/-- All `k`-element sublists. -/
def h069Subsets {α : Type} : List α → Nat → List (List α)
  | _, 0 => [[]]
  | [], _ + 1 => []
  | x :: xs, k + 1 => (h069Subsets xs k).map (x :: ·) ++ h069Subsets xs (k + 1)

theorem H069_subsets_length {α : Type} (xs : List α) :
    ∀ k, (h069Subsets xs k).length = h069Choose xs.length k := by
  induction xs with
  | nil => intro k; cases k <;> simp [h069Subsets, h069Choose]
  | cons x xs ih =>
    intro k
    cases k with
    | zero => simp [h069Subsets, h069Choose]
    | succ k =>
      simp only [h069Subsets, List.length_append, List.length_map, ih, List.length_cons,
        h069Choose]

theorem H069_threshold {α : Type} (Vp : List α) (m N : Nat) (sumF : List α → Nat)
    (h : ∀ t, t < N → ∃ s ∈ h069Subsets Vp (m - 1), sumF s = t) :
    N ≤ h069Choose Vp.length (m - 1) := by
  have hc : ∀ t, t < N → t ∈ (h069Subsets Vp (m - 1)).map sumF := by
    intro t ht
    obtain ⟨s, hs, hst⟩ := h t ht
    exact List.mem_map.mpr ⟨s, hs, hst⟩
  have := b07_cover_le N _ hc
  simpa [H069_subsets_length] using this

def H069_claim : Prop :=
  ∀ {α : Type} (Vp : List α) (m N : Nat) (sumF : List α → Nat),
    (∀ t, t < N → ∃ s ∈ h069Subsets Vp (m - 1), sumF s = t) →
    N ≤ h069Choose Vp.length (m - 1)

theorem H069_claim_holds : H069_claim := fun Vp m N sumF h =>
  H069_threshold Vp m N sumF h

theorem H069_instance : h069Choose 5 2 = 10 ∧ h069Choose 6 3 = 20 := by decide

/-! ## H070 -/

/-- **H070** — Kloosterman/Weil yield bound for codimension-c descent targets.
Handbook 10.1.4.4, 10.1.3.  Phase: descent.  Claim: the indicator of the
codimension-`c` subspace cut out by `c` parity bits is `2^-c` times a product
of characters `(1 + (-1)^b_j)`, i.e. a character sum; the Weil bound on the
non-trivial characters is a hypothesis and is not proved here. -/
def h070Sgn (b : Nat) : Int := if b % 2 = 0 then 1 else -1

def h070Prod : List Nat → Int
  | [] => 1
  | b :: bs => (1 + h070Sgn b) * h070Prod bs

theorem H070_indicator_expansion (bs : List Nat) :
    h070Prod bs = if bs.all (fun b => b % 2 == 0) then (2 : Int) ^ bs.length else 0 := by
  induction bs with
  | nil => simp [h070Prod]
  | cons b bs ih =>
    simp only [h070Prod, ih, List.all_cons, List.length_cons]
    by_cases hb : b % 2 = 0
    · simp [h070Sgn, hb, Int.pow_succ]
      split <;> simp [Int.mul_comm]
    · simp [h070Sgn, hb]

theorem H070_single_bit (b : Nat) :
    2 * (if b % 2 = 0 then (1 : Int) else 0) = 1 + h070Sgn b := by
  unfold h070Sgn; split <;> omega

def H070_claim : Prop :=
  ∀ bs : List Nat, h070Prod bs = if bs.all (fun b => b % 2 == 0) then (2 : Int) ^ bs.length else 0

theorem H070_claim_holds : H070_claim := H070_indicator_expansion

end HandbookIC.Ideas.B07

#print axioms HandbookIC.Ideas.B07.b07_nodup_le
#print axioms HandbookIC.Ideas.B07.b07_cover_le
#print axioms HandbookIC.Ideas.B07.b07_flatMap_length
#print axioms HandbookIC.Ideas.B07.H061_relation_character
#print axioms HandbookIC.Ideas.B07.H061_patterns_length
#print axioms HandbookIC.Ideas.B07.H061_survivors_m3
#print axioms HandbookIC.Ideas.B07.H061_survivors_m4
#print axioms HandbookIC.Ideas.B07.H061_survivors_half_m3
#print axioms HandbookIC.Ideas.B07.H062_flatten_len
#print axioms HandbookIC.Ideas.B07.H062_cover_bound
#print axioms HandbookIC.Ideas.B07.H062_orbit_cover_bound
#print axioms HandbookIC.Ideas.B07.H062_claim_holds
#print axioms HandbookIC.Ideas.B07.H063_rot_length
#print axioms HandbookIC.Ideas.B07.H063_lexLe_lz
#print axioms HandbookIC.Ideas.B07.H063_claim_holds
#print axioms HandbookIC.Ideas.B07.H063_instance
#print axioms HandbookIC.Ideas.B07.H064_cost_lt_replication
#print axioms HandbookIC.Ideas.B07.H064_decode_any_two
#print axioms HandbookIC.Ideas.B07.H064_claim_holds
#print axioms HandbookIC.Ideas.B07.H065_first_ge
#print axioms HandbookIC.Ideas.B07.H065_first_le
#print axioms HandbookIC.Ideas.B07.H065_first_mono
#print axioms HandbookIC.Ideas.B07.H065_linComp_mono
#print axioms HandbookIC.Ideas.B07.H065_linComp_le
#print axioms HandbookIC.Ideas.B07.H065_saving
#print axioms HandbookIC.Ideas.B07.H065_claim_holds
#print axioms HandbookIC.Ideas.B07.H066_functional_comb
#print axioms HandbookIC.Ideas.B07.H066_matvec_count
#print axioms HandbookIC.Ideas.B07.H066_claim_holds
#print axioms HandbookIC.Ideas.B07.H067_count_le
#print axioms HandbookIC.Ideas.B07.H067_claim_holds
#print axioms HandbookIC.Ideas.B07.H067_instance
#print axioms HandbookIC.Ideas.B07.H068_tuples_length
#print axioms HandbookIC.Ideas.B07.H068_cover_count
#print axioms HandbookIC.Ideas.B07.H068_necessary
#print axioms HandbookIC.Ideas.B07.H068_claim_holds
#print axioms HandbookIC.Ideas.B07.H069_subsets_length
#print axioms HandbookIC.Ideas.B07.H069_threshold
#print axioms HandbookIC.Ideas.B07.H069_claim_holds
#print axioms HandbookIC.Ideas.B07.H069_instance
#print axioms HandbookIC.Ideas.B07.H070_indicator_expansion
#print axioms HandbookIC.Ideas.B07.H070_single_bit
#print axioms HandbookIC.Ideas.B07.H070_claim_holds
