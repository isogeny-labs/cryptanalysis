import HandbookIC.Core

/-!
# HandbookIC.Ideas.B01 — handbook ideas H001 .. H010 (factor-base phase)

Each idea has: a doc comment, definitions prefixed by the lower-case id,
`def Hxxx_claim : Prop` (all hypotheses explicit, curve facts are hypotheses
or record fields, nothing is postulated) and at least one proved supporting theorem.
-/

namespace HandbookIC.Ideas.B01

open HandbookIC

/-! ## Shared helpers -/

/-- Number of items of `xs` whose key equals `r`. -/
def b01Bucket {α : Type} (key : α → Nat) (r : Nat) (xs : List α) : Nat :=
  (xs.filter (fun a => key a == r)).length

theorem b01_ite_sum (k R : Nat) :
    ((List.range R).map (fun r => if k == r then 1 else 0)).sum
      = if k < R then 1 else 0 := by
  induction R with
  | zero => simp
  | succ R ih =>
    rw [List.range_succ, List.map_append, List.sum_append, ih]
    simp only [List.map_cons, List.map_nil, List.sum_cons, List.sum_nil]
    by_cases h1 : k < R <;> by_cases h2 : k = R <;> simp [h1, h2] <;> omega

theorem b01_sum_zero {β : Type} (l : List β) : (l.map (fun _ => 0)).sum = 0 := by
  induction l with
  | nil => simp
  | cons x l ih => simp [ih]

theorem b01_sum_replicate (K c : Nat) : (List.replicate K c).sum = K * c := by
  induction K with
  | zero => simp
  | succ K ih => simp [List.replicate_succ, ih, Nat.succ_mul]; omega

theorem b01_sum_le {l : List Nat} {n : Nat} (h : ∀ x ∈ l, x ≤ n) :
    l.sum ≤ l.length * n := by
  induction l with
  | nil => simp
  | cons x l ih =>
    have h1 := h x (List.mem_cons_self)
    have h2 := ih (fun y hy => h y (List.mem_cons_of_mem x hy))
    simp only [List.sum_cons, List.length_cons, Nat.succ_mul]
    omega

/-- Double counting: bucket sizes over keys `< R` add up to the list length. -/
theorem b01_bucket_sum {α : Type} (key : α → Nat) (R : Nat) (xs : List α)
    (h : ∀ a ∈ xs, key a < R) :
    ((List.range R).map (fun r => b01Bucket key r xs)).sum = xs.length := by
  induction xs with
  | nil => simp [b01Bucket, b01_sum_zero]
  | cons a xs ih =>
    have ih' := ih (fun b hb => h b (List.mem_cons_of_mem a hb))
    have ha : key a < R := h a (List.mem_cons_self)
    have step : ∀ r, b01Bucket key r (a :: xs)
        = b01Bucket key r xs + (if key a == r then 1 else 0) := by
      intro r
      unfold b01Bucket
      by_cases e : (key a == r) = true
      · simp [List.filter_cons, e]
      · simp [List.filter_cons, e]
    have : (List.range R).map (fun r => b01Bucket key r (a :: xs))
        = (List.range R).map (fun r => b01Bucket key r xs + (if key a == r then 1 else 0)) := by
      apply List.map_congr_left
      intro r _
      exact step r
    rw [this]
    have hs : ∀ (l : List Nat) (f g : Nat → Nat),
        (l.map (fun r => f r + g r)).sum = (l.map f).sum + (l.map g).sum := by
      intro l f g
      induction l with
      | nil => simp
      | cons x l ih2 => simp [ih2]; omega
    rw [hs, ih', b01_ite_sum]
    simp [ha]

/-- Best element of a list of naturals (0 on the empty list). -/
def b01Best : List Nat → Nat
  | [] => 0
  | x :: xs => max x (b01Best xs)

theorem b01Best_ge_mem (xs : List Nat) (x : Nat) (h : x ∈ xs) : x ≤ b01Best xs := by
  induction xs with
  | nil => simp at h
  | cons y ys ih =>
    simp only [b01Best]
    rcases List.mem_cons.mp h with rfl | h'
    · exact Nat.le_max_left _ _
    · exact Nat.le_trans (ih h') (Nat.le_max_right _ _)

theorem b01Best_append_ge (xs ys : List Nat) : b01Best xs ≤ b01Best (xs ++ ys) := by
  induction xs with
  | nil => simp [b01Best]
  | cons y zs ih =>
    simp only [List.cons_append, b01Best]
    omega

/-! ## H001 -/

/-- **H001** — Kloosterman/Walsh ranking of affine cosets for the factor base.
Handbook 17.2.1 (Mutually unbiased bases). Phase: factor-base.
Claim: across the `2^(n-m)` cosets of a fixed `V`, valid-point counts exceed
binomial spread, and a Walsh dual-sum predictor with Spearman `≥ 0.6` gives a
best-of-64 gain `≥ 1.05x` relations per factor-base element. -/
structure H001Obs where
  n : Nat
  m : Nat
  /-- valid-point count per sampled coset, in predictor order (best predicted first) -/
  counts : List Nat
  spearmanMilli : Nat

/-- Gain (per mille) of taking the top-predicted coset over the mean coset. -/
def h001PickGainMilli (counts : List Nat) : Nat :=
  match counts with
  | [] => 0
  | c :: _ => 1000 * c * counts.length / counts.sum

/-- Partition of the point set into cosets. -/
def h001Partition {α : Type} (cosets : List (List α)) : List α := cosets.flatten

def H001_claim : Prop :=
  ∀ o : H001Obs, o.m ≤ o.n → o.counts.length = 64 → 600 ≤ o.spearmanMilli →
    1050 ≤ h001PickGainMilli o.counts

/-- Coset average equals total over number of cosets (counts add over a partition). -/
theorem H001_partition_sum {α : Type} (cosets : List (List α)) (smooth : α → Bool) :
    smoothCount (h001Partition cosets) smooth
      = (cosets.map (fun c => smoothCount c smooth)).sum := by
  unfold h001Partition
  induction cosets with
  | nil => simp [smoothCount]
  | cons c cs ih =>
    unfold smoothCount at *
    simp only [List.flatten_cons, List.filter_append, List.length_append, List.map_cons,
      List.sum_cons, ih]

/-- With equal coset counts the pick gain is exactly 1.000x: gains need variance. -/
theorem H001_no_gain_without_variance (K c : Nat) (hK : 0 < K) (hc : 0 < c) :
    h001PickGainMilli (List.replicate K c) = 1000 := by
  cases K with
  | zero => omega
  | succ K =>
    simp only [h001PickGainMilli, List.replicate_succ, List.length_cons,
      List.length_replicate, List.sum_cons, b01_sum_replicate]
    have : c + K * c = (K + 1) * c := by rw [Nat.succ_mul]; omega
    rw [this]
    have h2 : 1000 * c * (K + 1) = 1000 * ((K + 1) * c) := by
      rw [Nat.mul_assoc, Nat.mul_comm c (K + 1)]
    rw [h2]
    exact Nat.mul_div_cancel _ (Nat.mul_pos (Nat.succ_pos K) hc)

/-! ## H002 -/

/-- **H002** — Cyclic-shift window factor base: Frobenius merge factor about 2.
Handbook 17.1.6.3 (Linear polynomial dynamical systems). Phase: factor-base.
Claim: for a window `V = span{x,..,x^(2^(m-1))}`, Frobenius classes number
`|V|/c` with class sizes at most 3, so the column reduction is below 4. -/
def h002StayInWindow (m k v : Nat) : Bool := decide (v < 2 ^ (m - k))

def h002StayCount (m k : Nat) : Nat :=
  ((List.range (2 ^ m)).filter (h002StayInWindow m k)).length

def H002_claim : Prop :=
  ∀ (m : Nat) (classSizes : List Nat),
    0 < m → classSizes.sum = 2 ^ m → (∀ s ∈ classSizes, s ≤ 3) →
    2 ^ m < 4 * classSizes.length

theorem h002_filter_range_lt (N c : Nat) :
    ((List.range N).filter (fun v => decide (v < c))).length = min N c := by
  induction N with
  | zero => simp
  | succ N ih =>
    rw [List.range_succ, List.filter_append, List.length_append, ih]
    by_cases h : N < c
    · simp [h]; omega
    · simp [h]; omega

/-- Bit counting: elements whose `k`-shift stays in the window number `2^(m-k)`. -/
theorem H002_stay_count (m k : Nat) (hk : k ≤ m) : h002StayCount m k = 2 ^ (m - k) := by
  unfold h002StayCount h002StayInWindow
  rw [h002_filter_range_lt]
  have : 2 ^ (m - k) ≤ 2 ^ m := Nat.pow_le_pow_right (by omega) (by omega)
  omega

example : h002StayCount 4 1 = 8 := by decide

theorem H002_claim_holds : H002_claim := by
  intro m classSizes hm hsum hle
  have h1 : classSizes.sum ≤ classSizes.length * 3 := by
    exact b01_sum_le hle
  have hpos : 0 < 2 ^ m := Nat.two_pow_pos m
  omega

/-! ## H003 -/

/-- **H003** — Kneser/Freiman-extremal subspaces with small product span.
Handbook 16.7.2 / 16.7.3. Phase: factor-base. Claim: for `d`-dim subspaces
of GF(2^n), `n` prime, `dim(V*V) = 2d-1` iff `V` is an AP `u*span{1,w,..}`;
random subspaces give `min(n, d(d+1)/2)`. -/
def h003Sums (d : Nat) : List Nat :=
  (List.range d).flatMap (fun i => (List.range d).map (fun j => i + j))

def h003RandomDim (n d : Nat) : Nat := min n (d * (d + 1) / 2)

structure H003Sample where
  n : Nat
  d : Nat
  dimProd : Nat
  isAP : Bool

/-- Kneser lower bound and the equality characterisation as hypotheses. -/
def H003_claim : Prop :=
  ∀ (S : H003Sample) (kneser : 2 * S.d - 1 ≤ S.dimProd)
    (equalityChar : S.dimProd = 2 * S.d - 1 → S.isAP = true),
    1 ≤ S.d → (S.isAP = false → 2 * S.d - 1 < S.dimProd)

theorem H003_ap_sums (d s : Nat) (hd : 1 ≤ d) :
    s ∈ h003Sums d ↔ s < 2 * d - 1 := by
  unfold h003Sums
  simp only [List.mem_flatMap, List.mem_range, List.mem_map]
  constructor
  · rintro ⟨i, hi, j, hj, rfl⟩
    omega
  · intro hs
    by_cases h : s < d
    · exact ⟨0, by omega, s, h, by omega⟩
    · exact ⟨s - (d - 1), by omega, d - 1, by omega, by omega⟩

theorem H003_claim_holds : H003_claim := by
  intro S kneser eqc _ hnot
  have : S.dimProd ≠ 2 * S.d - 1 := fun h => by
    have := eqc h
    rw [hnot] at this
    cases this
  omega

theorem H003_ap_le_generic (d : Nat) : 2 * d - 1 ≤ d * (d + 1) / 2 := by
  cases d with
  | zero => simp
  | succ k =>
    rw [Nat.le_div_iff_mul_le (by decide)]
    have h1 : 2 * k ≤ (k + 1) * k := by
      cases k with
      | zero => simp
      | succ j => exact Nat.mul_le_mul_right _ (by omega)
    have e : (k + 1) * (k + 1 + 1) = (k + 1) * k + (k + 1) * 1 + (k + 1) * 1 := by
      rw [Nat.mul_add, Nat.mul_add]
    generalize (k + 1) * k = q at h1 e
    generalize (k + 1) * (k + 1 + 1) = r at e ⊢
    omega

example : h003RandomDim 23 7 = 23 := by decide
example : 2 * 7 - 1 = 13 := by decide

/-! ## H004 -/

/-- **H004** — Fano-factor selection of equal-size subspace factor bases.
Handbook 16.2.1. Phase: factor-base. Claim: the solution count `N(V)` over
random `k`-dim subspaces is over-dispersed, so best-of-`M` selection gives
`>= 1.2x` relations per candidate at fixed `|V|`. -/
structure H004Obs where
  baseCount : Nat   -- mean smooth count of a random V
  bestCount : Nat   -- smooth count of the best of M subspaces
  M : Nat

def h004RelationCost (need smooth trials : Nat) : Nat := expectedTrials need smooth trials

def H004_claim : Prop :=
  ∀ o : H004Obs, 0 < o.baseCount → 300 ≤ o.M → 1200 * o.baseCount ≤ 1000 * o.bestCount

theorem H004_cost_divides (need p t c : Nat) :
    h004RelationCost need (c * p) t = h004RelationCost need p t / c := by
  unfold h004RelationCost expectedTrials
  rw [Nat.div_div_eq_div_mul, Nat.mul_comm p c]

theorem H004_cost_antitone (need p t c : Nat) (hp : 0 < p) (hc : 1 ≤ c) :
    h004RelationCost need (c * p) t ≤ h004RelationCost need p t := by
  rw [H004_cost_divides]
  exact Nat.div_le_self _ _

theorem H004_cost_improves (c c' : Cost) (need p t k : Nat) (hk : 2 ≤ k)
    (hpos : 0 < h004RelationCost need p t)
    (h1 : c.relations = h004RelationCost need p t)
    (h2 : c'.relations = h004RelationCost need (k * p) t)
    (h3 : c'.factorBase = c.factorBase) (h4 : c'.linearAlgebra = c.linearAlgebra)
    (h5 : c'.descent = c.descent) : c.improvesRelations c' := by
  refine ⟨h3, h4, h5, ?_⟩
  rw [h1, h2, H004_cost_divides]
  exact Nat.div_lt_self hpos hk

/-! ## H005 -/

/-- **H005** — Trace-code rank-profile criterion for factor-base subspace shape.
Handbook 15.1.2.4 / 15.1.2.3. Phase: factor-base. Claim: at fixed dimension,
the dispersion of decomposition counts differs across `V` shapes, and
`P(N0 >= 1)` differs by `>= 0.03` between the best and worst shape. -/
structure H005Shape where
  name : Nat
  pAtLeastOneMilli : Nat   -- P(N0 >= 1) per mille

def h005Spread (shapes : List H005Shape) : Nat :=
  b01Best (shapes.map (·.pAtLeastOneMilli))

def H005_claim : Prop :=
  ∀ (shapes : List H005Shape) (best worst : H005Shape),
    best ∈ shapes → worst ∈ shapes →
    best.pAtLeastOneMilli = h005Spread shapes →
    (∀ s ∈ shapes, worst.pAtLeastOneMilli ≤ s.pAtLeastOneMilli) →
    worst.pAtLeastOneMilli + 30 ≤ best.pAtLeastOneMilli

/-- Double counting: `sum_r N0(r) = number of pairs`, for any pair-to-`r` map. -/
theorem H005_sum_counts {P : Type} (pairs : List P) (rOf : P → Nat) (R : Nat)
    (h : ∀ p ∈ pairs, rOf p < R) :
    ((List.range R).map (fun r => b01Bucket rOf r pairs)).sum = pairs.length :=
  b01_bucket_sum rOf R pairs h

theorem H005_best_ge (shapes : List H005Shape) (s : H005Shape) (h : s ∈ shapes) :
    s.pAtLeastOneMilli ≤ h005Spread shapes :=
  b01Best_ge_mem _ _ (List.mem_map.mpr ⟨s, h, rfl⟩)

/-! ## H006 -/

/-- **H006** — Cyclotomic-coset factor base `x^s in C`.
Handbook 14.7.1 / 14.6.5. Phase: factor-base. Model: `GF(2^n)*` is `Z/N`
(`N = 2^n-1`) via the log, `x^s` is `i -> s*i mod N`, Frobenius is doubling.
Claim: `F` is Frobenius-stable when `C` is, and `|F| = s*n` when `C` is an
orbit of `n` elements and `s` divides `N`. -/
def h006InF (N s : Nat) (C : Nat → Bool) (i : Nat) : Bool := C (s * i % N)

def h006Card (N s : Nat) (C : Nat → Bool) : Nat :=
  ((List.range N).filter (h006InF N s C)).length

def h006Orbit (N s n : Nat) : Nat → Bool :=
  fun c => (List.range n).any (fun k => c == s * 2 ^ k % N)

def H006_claim : Prop :=
  ∀ (N s n : Nat), 0 < N → N % s = 0 → 0 < s →
    (∀ c, h006Orbit N s n c = true → h006Orbit N s n (2 * c % N) = true) →
    (∀ i, h006InF N s (h006Orbit N s n) i = true →
        h006InF N s (h006Orbit N s n) (2 * i % N) = true) ∧
    (n = (List.range n).length) ∧
    (-- |F| = s*n, assuming the orbit has exactly n distinct elements
      ((List.range N).filter (fun c => h006Orbit N s n c)).length = n →
      h006Card N s (h006Orbit N s n) = s * n)

/-- Stability of `F` under doubling follows from stability of `C`. -/
theorem H006_stable (N s : Nat) (C : Nat → Bool)
    (hC : ∀ c, C c = true → C (2 * c % N) = true) (i : Nat)
    (h : h006InF N s C i = true) : h006InF N s C (2 * i % N) = true := by
  unfold h006InF at *
  have e : s * (2 * i % N) % N = 2 * (s * i % N) % N := by
    rw [Nat.mul_mod_mod, Nat.mul_mod_mod, Nat.mul_left_comm]
  rw [e]
  exact hC _ h

/-- Instance check: `n = 6`, `N = 63`, `s = 3` gives `|F| = 18 = s*n`. -/
theorem H006_instance : h006Card 63 3 (h006Orbit 63 3 6) = 18 := by decide

/-! ## H007 -/

/-- **H007** — 2-torsion translation as extra projectivity in the orbit quotient.
Handbook 14.4.2. Phase: factor-base. Claim: quotienting by `<Frobenius, iota>`
(order `2d`) instead of `<Frobenius>` (order `d`) halves unknown classes and
relations needed. -/
def h007Classes (N d : Nat) : Nat := orbitRepresentatives N d

def h007Cost (N d perClass : Nat) (rest : Cost) : Cost :=
  { rest with relations := h007Classes N d * perClass }

def H007_claim : Prop :=
  ∀ (N d : Nat) (classesPi classesPiIota : Nat),
    0 < d → d ∣ N → classesPi = h007Classes N d → classesPiIota = h007Classes N (2 * d) →
    2 * classesPiIota ≤ classesPi

theorem H007_monotone (N d : Nat) : h007Classes N (2 * d) ≤ h007Classes N d := by
  unfold h007Classes orbitRepresentatives
  cases d with
  | zero => simp
  | succ d => exact Nat.div_le_div_left (by omega) (by omega)

theorem H007_half (N d : Nat) : h007Classes N (2 * d) = h007Classes N d / 2 := by
  unfold h007Classes orbitRepresentatives
  rw [Nat.div_div_eq_div_mul, Nat.mul_comm]

theorem H007_claim_holds : H007_claim := by
  intro N d a b _ _ ha hb
  subst ha hb
  rw [H007_half]
  omega

theorem H007_cost_improves (N d perClass : Nat) (rest : Cost)
    (hpos : 0 < h007Classes N (2 * d) * perClass)
    (h : 0 < perClass) (hs : h007Classes N (2 * d) < h007Classes N d) :
    (h007Cost N d perClass rest).improvesRelations (h007Cost N (2 * d) perClass rest) := by
  refine ⟨rfl, rfl, rfl, ?_⟩
  show h007Classes N (2 * d) * perClass < h007Classes N d * perClass
  exact Nat.mul_lt_mul_of_pos_right hs h

/-! ## H008 -/

/-- **H008** — Exponential-sum bias of the S3 triple count `T(V)`.
Handbook 12.5.3 / 12.7.3. Phase: factor-base. Claim: `T(V)` varies beyond
clumped Poisson across `V`; best of 1000 gives `1.2-1.5x` the mean. -/
def h008Count {α : Type} (B : Nat) (F : Nat → α) (rel : α → α → α → Bool) : Nat :=
  ((List.range B).map (fun i => ((List.range B).map (fun j =>
    ((List.range B).filter (fun k => rel (F i) (F j) (F k))).length)).sum)).sum

structure H008Obs where
  meanT : Nat
  bestT : Nat
  trials : Nat

def H008_claim : Prop :=
  ∀ o : H008Obs, 0 < o.meanT → o.trials = 1000 → 1200 * o.meanT ≤ 1000 * o.bestT

theorem h008_sum_le (l : List Nat) (n : Nat) (h : ∀ x ∈ l, x ≤ n) :
    l.sum ≤ l.length * n := by
  exact b01_sum_le h

/-- `T(V) <= B^3`. -/
theorem H008_le_cube {α : Type} (B : Nat) (F : Nat → α) (rel : α → α → α → Bool) :
    h008Count B F rel ≤ B ^ 3 := by
  unfold h008Count
  have inner : ∀ i, ((List.range B).map (fun j =>
      ((List.range B).filter (fun k => rel (F i) (F j) (F k))).length)).sum ≤ B * B := by
    intro i
    have := h008_sum_le ((List.range B).map (fun j =>
      ((List.range B).filter (fun k => rel (F i) (F j) (F k))).length)) B (by
        intro x hx
        obtain ⟨j, _, rfl⟩ := List.mem_map.mp hx
        have := List.length_filter_le (fun k => rel (F i) (F j) (F k)) (List.range B)
        simpa using this)
    simpa using this
  have := h008_sum_le ((List.range B).map (fun i => ((List.range B).map (fun j =>
      ((List.range B).filter (fun k => rel (F i) (F j) (F k))).length)).sum)) (B * B) (by
        intro x hx
        obtain ⟨i, _, rfl⟩ := List.mem_map.mp hx
        exact inner i)
  simp only [List.length_map, List.length_range] at this
  have e : B ^ 3 = B * (B * B) := by
    rw [Nat.pow_succ, Nat.pow_succ, Nat.pow_one, Nat.mul_assoc]
  rw [e]; exact this

/-- Cost.relations is antitone in the triple count. -/
theorem H008_cost_antitone (need t T T' : Nat) (hT : 0 < T) (h : T ≤ T') :
    expectedTrials need T' t ≤ expectedTrials need T t := by
  unfold expectedTrials
  exact Nat.div_le_div_left h hT

/-- One-index permutation invariance of a count. -/
theorem H008_perm_invariant (B : Nat) (σ : Nat → Nat)
    (hσ : ((List.range B).map σ).Perm (List.range B)) (p : Nat → Bool) :
    ((List.range B).filter (fun k => p (σ k))).length
      = ((List.range B).filter p).length := by
  have h1 : (((List.range B).map σ).filter p).length = ((List.range B).filter p).length :=
    (hσ.filter p).length_eq
  have h2 : ((List.range B).map σ).filter p
      = ((List.range B).filter (p ∘ σ)).map σ := by
    rw [List.filter_map]
  rw [h2, List.length_map] at h1
  exact h1

/-! ## H009 -/

/-- **H009** — Artin-Schreier splitting density of cosets of `V`.
Handbook 12.1.3. Phase: factor-base. Claim: the fraction of useful
`m`-tuples is the `m`-th power of the per-element on-curve density, so a
coset of density `rho` improves useful tuples by `(rho/0.5)^m`. -/
def h009Tuples {α : Type} : Nat → List α → List (List α)
  | 0, _ => [[]]
  | m + 1, xs => xs.flatMap (fun a => (h009Tuples m xs).map (fun t => a :: t))

def h009Good {α : Type} (m : Nat) (xs : List α) (onCurve : α → Bool) : Nat :=
  (h009Tuples m (xs.filter onCurve)).length

theorem h009_flat_length {α : Type} (xs : List α) (ys : List (List α)) :
    (xs.flatMap (fun a => ys.map (fun t => a :: t))).length = xs.length * ys.length := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    simp [List.flatMap_cons, ih, Nat.succ_mul]
    omega

theorem h009_tuples_length {α : Type} (m : Nat) (xs : List α) :
    (h009Tuples m xs).length = xs.length ^ m := by
  induction m with
  | zero => simp [h009Tuples]
  | succ m ih =>
    simp only [h009Tuples]
    rw [h009_flat_length, ih, Nat.pow_succ, Nat.mul_comm]

/-- Useful `m`-tuples number (on-curve count)^m. -/
theorem H009_good_count {α : Type} (m : Nat) (xs : List α) (onCurve : α → Bool) :
    h009Good m xs onCurve = (smoothCount xs onCurve) ^ m := by
  unfold h009Good smoothCount
  exact h009_tuples_length m _

/-- A coset with more on-curve points gives at least as many useful tuples. -/
theorem H009_monotone {α : Type} (m : Nat) (xs ys : List α) (p q : α → Bool)
    (h : smoothCount xs p ≤ smoothCount ys q) :
    h009Good m xs p ≤ h009Good m ys q := by
  rw [H009_good_count, H009_good_count]
  exact Nat.pow_le_pow_left h m

def H009_claim : Prop :=
  ∀ (m k : Nat) (xs : List Nat) (onCurve : Nat → Bool),
    xs.length = 2 ^ k → 0 < m →
    h009Good m xs onCurve * (xs.length) ^ m = (smoothCount xs onCurve) ^ m * (xs.length) ^ m ∧
    (2 * smoothCount xs onCurve ≥ xs.length + 1 →
       xs.length ^ m < 2 ^ m * h009Good m xs onCurve)

/-! ## H010 -/

/-- **H010** — Legendre-sequence bias selection of affine cosets.
Handbook 10.4.4.3. Phase: factor-base. Claim: with `chi in {+1,-1}`, lift
fraction `= 1/2 + (1/(2|V|)) sum chi`, and best-of-`T` coset selection never
lowers it (gain `~0.35 sqrt(ln T/|V|)`, toy-scale only). -/
def h010Chi (b : Bool) : Int := if b then 1 else -1

def h010SumChi (bs : List Bool) : Int := (bs.map h010Chi).sum

def h010Lifts (bs : List Bool) : Nat := (bs.filter id).length

def h010BestOfT (fractions : List Nat) : Nat := b01Best fractions

def H010_claim : Prop :=
  ∀ (bs : List Bool), 2 * (h010Lifts bs : Int) = (bs.length : Int) + h010SumChi bs

theorem H010_claim_holds : H010_claim := by
  intro bs
  unfold h010Lifts h010SumChi h010Chi
  induction bs with
  | nil => simp
  | cons b bs ih =>
    cases b <;> simp [List.filter_cons] <;> omega

theorem H010_best_monotone (xs ys : List Nat) :
    h010BestOfT xs ≤ h010BestOfT (xs ++ ys) := b01Best_append_ge xs ys

theorem H010_best_ge (xs : List Nat) (x : Nat) (h : x ∈ xs) : x ≤ h010BestOfT xs :=
  b01Best_ge_mem xs x h

end HandbookIC.Ideas.B01

#print axioms HandbookIC.Ideas.B01.b01_ite_sum
#print axioms HandbookIC.Ideas.B01.b01_sum_zero
#print axioms HandbookIC.Ideas.B01.b01_sum_replicate
#print axioms HandbookIC.Ideas.B01.b01_sum_le
#print axioms HandbookIC.Ideas.B01.b01_bucket_sum
#print axioms HandbookIC.Ideas.B01.b01Best_ge_mem
#print axioms HandbookIC.Ideas.B01.b01Best_append_ge
#print axioms HandbookIC.Ideas.B01.H001_partition_sum
#print axioms HandbookIC.Ideas.B01.H001_no_gain_without_variance
#print axioms HandbookIC.Ideas.B01.h002_filter_range_lt
#print axioms HandbookIC.Ideas.B01.H002_stay_count
#print axioms HandbookIC.Ideas.B01.H002_claim_holds
#print axioms HandbookIC.Ideas.B01.H003_ap_sums
#print axioms HandbookIC.Ideas.B01.H003_claim_holds
#print axioms HandbookIC.Ideas.B01.H003_ap_le_generic
#print axioms HandbookIC.Ideas.B01.H004_cost_divides
#print axioms HandbookIC.Ideas.B01.H004_cost_antitone
#print axioms HandbookIC.Ideas.B01.H004_cost_improves
#print axioms HandbookIC.Ideas.B01.H005_sum_counts
#print axioms HandbookIC.Ideas.B01.H005_best_ge
#print axioms HandbookIC.Ideas.B01.H006_stable
#print axioms HandbookIC.Ideas.B01.H006_instance
#print axioms HandbookIC.Ideas.B01.H007_monotone
#print axioms HandbookIC.Ideas.B01.H007_half
#print axioms HandbookIC.Ideas.B01.H007_claim_holds
#print axioms HandbookIC.Ideas.B01.H007_cost_improves
#print axioms HandbookIC.Ideas.B01.h008_sum_le
#print axioms HandbookIC.Ideas.B01.H008_le_cube
#print axioms HandbookIC.Ideas.B01.H008_cost_antitone
#print axioms HandbookIC.Ideas.B01.H008_perm_invariant
#print axioms HandbookIC.Ideas.B01.h009_flat_length
#print axioms HandbookIC.Ideas.B01.h009_tuples_length
#print axioms HandbookIC.Ideas.B01.H009_good_count
#print axioms HandbookIC.Ideas.B01.H009_monotone
#print axioms HandbookIC.Ideas.B01.H010_claim_holds
#print axioms HandbookIC.Ideas.B01.H010_best_monotone
#print axioms HandbookIC.Ideas.B01.H010_best_ge
