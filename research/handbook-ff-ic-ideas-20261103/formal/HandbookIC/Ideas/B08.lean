import HandbookIC.Core

/-!
# HandbookIC.Ideas.B08 — handbook ideas H071 .. H080 (descent and cost model)

Each idea has: a doc comment, definitions prefixed by the lower-case id,
`def Hxxx_claim : Prop` (all hypotheses explicit; curve and measurement facts
are record fields or hypotheses, nothing is postulated) and proved supporting
theorems.
-/

namespace HandbookIC.Ideas.B08

open HandbookIC

/-! ## H071 -/

/-- **H071** — Bilinear dreg and time of the 2-point descent system.
Handbook 9.1.1.1 (Algebraic normal form), 9.2.7 (Quadratic APN functions).
Phase: descent. Claim: with `r` fixed the descent system is bilinear in two
bit blocks, so fixing `x1` leaves an affine system in `x2`; F4 `dreg ≤ d+1`
lies at least one below the semi-regular prediction for `n ≥ 21`, and the
log2 time slope per bit is below the enumeration slope. -/
def h071XorSum : (n : Nat) → (Fin n → Bool) → Bool
  | 0, _ => false
  | n + 1, f => xor (h071XorSum n (fun i => f i.castSucc)) (f (Fin.last n))

theorem h071XorSum_xor : ∀ (n : Nat) (f g : Fin n → Bool),
    h071XorSum n (fun i => xor (f i) (g i)) = xor (h071XorSum n f) (h071XorSum n g)
  | 0, f, g => by simp [h071XorSum]
  | n + 1, f, g => by
      simp only [h071XorSum]
      rw [h071XorSum_xor n (fun i => f i.castSucc) (fun i => g i.castSucc)]
      generalize h071XorSum n (fun i => f i.castSucc) = a
      generalize h071XorSum n (fun i => g i.castSucc) = b
      generalize f (Fin.last n) = c
      generalize g (Fin.last n) = e
      cases a <;> cases b <;> cases c <;> cases e <;> rfl

/-- A bilinear form over GF(2) on `n`-bit by `m`-bit blocks. -/
def h071Bil (n m : Nat) (M : Fin n → Fin m → Bool) (x : Fin n → Bool)
    (y : Fin m → Bool) : Bool :=
  h071XorSum n (fun i => x i && h071XorSum m (fun j => M i j && y j))

theorem h071_and_xor (a b c : Bool) : (a && xor b c) = xor (a && b) (a && c) := by
  cases a <;> cases b <;> cases c <;> rfl

/-- Fixing `x1`, the bilinear form is additive (affine) in `x2`. -/
theorem H071_affine_in_x2 (n m : Nat) (M : Fin n → Fin m → Bool)
    (x : Fin n → Bool) (y z : Fin m → Bool) :
    h071Bil n m M x (fun j => xor (y j) (z j))
      = xor (h071Bil n m M x y) (h071Bil n m M x z) := by
  unfold h071Bil
  have h1 : ∀ i, h071XorSum m (fun j => M i j && xor (y j) (z j))
      = xor (h071XorSum m (fun j => M i j && y j))
            (h071XorSum m (fun j => M i j && z j)) := by
    intro i
    rw [← h071XorSum_xor]
    congr 1
    funext j
    exact h071_and_xor _ _ _
  have h2 : (fun i => x i && h071XorSum m (fun j => M i j && xor (y j) (z j)))
      = fun i => xor (x i && h071XorSum m (fun j => M i j && y j))
                     (x i && h071XorSum m (fun j => M i j && z j)) := by
    funext i
    rw [h1 i, h071_and_xor]
  rw [h2]
  exact h071XorSum_xor n (fun i => x i && h071XorSum m (fun j => M i j && y j))
    (fun i => x i && h071XorSum m (fun j => M i j && z j))

/-- Descent cost model: `2^d` choices of `x1`, each an affine solve of cost `perX1`. -/
def h071Descent (d perX1 : Nat) : Nat := 2 ^ d * perX1

theorem H071_descent_bound (n d perX1 : Nat) (h : perX1 ≤ n * d * d) :
    h071Descent d perX1 ≤ 2 ^ d * n * d * d := by
  unfold h071Descent
  calc 2 ^ d * perX1 ≤ 2 ^ d * (n * d * d) := Nat.mul_le_mul_left _ h
    _ = 2 ^ d * n * d * d := by simp only [Nat.mul_assoc]

theorem H071_cost_total (c : Cost) (n d : Nat) (h : c.descent ≤ 2 ^ d * n * d * d) :
    c.total ≤ c.factorBase + c.relations + c.linearAlgebra + 2 ^ d * n * d * d := by
  unfold Cost.total
  omega

/-- A measurement record of F4 on Weil-restricted descent systems. -/
structure h071Measure where
  dreg : Nat → Nat
  dregSemi : Nat → Nat
  logTimeF4 : Nat → Nat
  logTimeEnum : Nat → Nat
  fromBilinearDescent : Nat → Prop

def h071d (n : Nat) : Nat := (n + 1) / 2 + 2

def H071_claim : Prop :=
  ∀ m : h071Measure,
    (∀ n, 17 ≤ n → n ≤ 29 → m.fromBilinearDescent n) →
    (∀ n, 17 ≤ n → n ≤ 29 → m.dreg n ≤ h071d n + 1) ∧
    (∀ n, 21 ≤ n → n ≤ 29 → m.dreg n + 1 ≤ m.dregSemi n) ∧
    m.logTimeF4 29 + m.logTimeEnum 17 < m.logTimeEnum 29 + m.logTimeF4 17

/-! ## H072 -/

/-- **H072** — Descent chain chosen by per-level valid-point fraction.
Handbook 9.1.2 (Walsh transform), 9.1.3 (Parameters of Boolean functions).
Phase: descent. Claim: among nested invariant chains of fixed dimensions the
per-level success counts vary beyond binomial noise, so the best chain has at
least 2x fewer expected trials than the median chain. -/
def h072Descent (N : Nat) : List Nat → Nat
  | [] => 0
  | c :: cs => N / c + h072Descent N cs

/-- Componentwise domination: every count of `cs` is at least the matching count of
`cs'`, and the counts of `cs'` are positive. -/
def h072Dom : List Nat → List Nat → Prop
  | [], [] => True
  | c :: cs, c' :: cs' => c' ≤ c ∧ 0 < c' ∧ h072Dom cs cs'
  | _, _ => False

theorem H072_monotone (N : Nat) : ∀ (cs cs' : List Nat),
    h072Dom cs cs' → h072Descent N cs ≤ h072Descent N cs'
  | [], [], _ => by simp [h072Descent]
  | [], _ :: _, h => by simp [h072Dom] at h
  | _ :: _, [], h => by simp [h072Dom] at h
  | c :: cs, c' :: cs', h => by
    simp only [h072Dom] at h
    simp only [h072Descent]
    have h1 := Nat.div_le_div_left (a := N) h.1 h.2.1
    have h2 := H072_monotone N cs cs' h.2.2
    omega

theorem H072_cost_total (c c' : Cost) (N : Nat) (cs cs' : List Nat)
    (h : h072Dom cs cs')
    (hc : c.descent = h072Descent N cs) (hc' : c'.descent = h072Descent N cs')
    (h1 : c'.factorBase = c.factorBase) (h2 : c'.relations = c.relations)
    (h3 : c'.linearAlgebra = c.linearAlgebra) :
    c.total ≤ c'.total := by
  have := H072_monotone N cs cs' h
  unfold Cost.total
  omega

def H072_claim : Prop :=
  ∀ (N : Nat) (chains : List (List Nat)) (med : Nat),
    chains.length = 500 →
    (∀ c ∈ chains, ∀ x ∈ c, 0 < x) →
    chains.length ≤ 2 * (chains.filter (fun c => decide (med ≤ h072Descent N c))).length →
    ∃ best ∈ chains, 2 * h072Descent N best ≤ med

/-! ## H073 -/

/-- **H073** — Per-level liftable-bias selection of descent sets.
Handbook 7.1.4 (Artin-Schreier hypersurfaces), 6.3.4.2 (Inversive congruential
pseudorandom numbers). Phase: descent. Claim: best-of-T selection of each
level's `V` by liftable bias cuts attempts per node by `(2 liftFrac)^(-m)` and
the total descent cost by about 2.5x (at least 1.15x). Fractions are in permille. -/
def h073Biased (m R lf : Nat) : Nat := R * 1000 ^ m / (2 * lf) ^ m

theorem H073_biased_le (m R lf : Nat) (h : 500 ≤ lf) : h073Biased m R lf ≤ R := by
  unfold h073Biased
  have hpos : 0 < 1000 ^ m := Nat.pow_pos (by decide)
  have hle : 1000 ^ m ≤ (2 * lf) ^ m := Nat.pow_le_pow_left (by omega) m
  calc R * 1000 ^ m / (2 * lf) ^ m ≤ R * 1000 ^ m / 1000 ^ m :=
        Nat.div_le_div_left hle hpos
    _ = R := Nat.mul_div_cancel R hpos

/-- Total work: nodes times attempts per node, summed over levels. -/
def h073Work : List Nat → List Nat → Nat
  | n :: ns, a :: as => n * a + h073Work ns as
  | _, _ => 0

def h073Le : List Nat → List Nat → Prop
  | [], [] => True
  | x :: xs, y :: ys => x ≤ y ∧ h073Le xs ys
  | _, _ => False

theorem H073_work_mono : ∀ (ns a' a : List Nat),
    h073Le a' a → h073Work ns a' ≤ h073Work ns a
  | [], _, _, _ => by simp [h073Work]
  | _ :: _, [], [], _ => by simp [h073Work]
  | _ :: _, [], _ :: _, _ => by simp [h073Work]
  | _ :: _, _ :: _, [], h => by simp [h073Le] at h
  | n :: ns, x :: xs, y :: ys, h => by
    simp only [h073Le] at h
    simp only [h073Work]
    have h1 := Nat.mul_le_mul_left n h.1
    have h2 := H073_work_mono ns xs ys h.2
    omega

structure h073Level where
  nodes : Nat
  randAtt : Nat
  chosenAtt : Nat
  lift : Nat

def H073_claim : Prop :=
  ∀ (m : Nat) (lv : List h073Level),
    lv ≠ [] → (∀ l ∈ lv, 500 ≤ l.lift) →
    100 * (lv.map (fun l => l.nodes * l.chosenAtt)).sum
      + 15 * (lv.map (fun l => l.nodes * l.chosenAtt)).sum
      ≤ 100 * (lv.map (fun l => l.nodes * l.randAtt)).sum ∧
    ∀ l ∈ lv,
      80 * (l.chosenAtt * (2 * l.lift) ^ m) ≤ 100 * (l.randAtt * 1000 ^ m) ∧
      100 * (l.randAtt * 1000 ^ m) ≤ 120 * (l.chosenAtt * (2 * l.lift) ^ m)

/-! ## H074 -/

/-- **H074** — Completely normal element for conversion-free subfield-tower descent.
Handbook 5.4.1 (Complete normal basis theorem), 5.4.3 (Cyclotomic modules and
complete generators). Phase: descent. Claim: a completely normal `β` is normal
over every `F_{2^d}`, `d ∣ n`, so successive Weil restrictions need no basis
conversion; composite `n` only. Modelled by a GF(2) circulant-rank proxy: for
each divisor `d`, the `n/d` rotations of `β` by multiples of `d` have full rank. -/
def h074Mask (n : Nat) : Nat := 2 ^ n - 1

def h074Rot (n v : Nat) : Nat := ((v <<< 1) ||| (v >>> (n - 1))) &&& h074Mask n

def h074RotK (n : Nat) : Nat → Nat → Nat
  | 0, v => v
  | k + 1, v => h074RotK n k (h074Rot n v)

def h074Rows (n d v : Nat) : List Nat :=
  (List.range (n / d)).map (fun k => h074RotK n (d * k) v)

/-- Insert into a descending xor basis. -/
def h074Ins (x : Nat) : List Nat → List Nat
  | [] => [x]
  | b :: bs => if x ≤ b then b :: h074Ins x bs else x :: b :: bs

def h074Add (basis : List Nat) (x : Nat) : List Nat :=
  let y := basis.foldl (fun a b => min a (a ^^^ b)) x
  if y = 0 then basis else h074Ins y basis

/-- GF(2) rank of a list of bitmask rows. -/
def h074Rank (rows : List Nat) : Nat := (rows.foldl h074Add []).length

def h074CN (n v : Nat) : Bool :=
  decide (v ≠ 0) &&
  (List.range (n + 1)).all (fun d => d == 0 || n % d != 0 || h074Rank (h074Rows n d v) == n / d)

def IsCompletelyNormalB08 (n v : Nat) : Prop := h074CN n v = true

/-- Basis-conversion cost model: `levels` conversions of about `n^2/64` word ops. -/
def h074Conv (n levels : Nat) : Nat := levels * (n * n / 64)

theorem H074_normal_of_cn (n v : Nat) (hn : 1 ≤ n) (h : IsCompletelyNormalB08 n v) :
    h074Rank (h074Rows n 1 v) = n := by
  unfold IsCompletelyNormalB08 h074CN at h
  simp only [Bool.and_eq_true, List.all_eq_true, Bool.or_eq_true, beq_iff_eq,
    bne_iff_ne, ne_eq, decide_eq_true_eq] at h
  have h1 := h.2 1 (List.mem_range.mpr (by omega))
  have hm : n % 1 = 0 := Nat.mod_one n
  rcases h1 with (h1 | h1) | h1
  · omega
  · exact absurd hm h1
  · simpa using h1

theorem H074_nonzero_of_cn (n v : Nat) (h : IsCompletelyNormalB08 n v) : v ≠ 0 := by
  unfold IsCompletelyNormalB08 h074CN at h
  simp only [Bool.and_eq_true, decide_eq_true_eq] at h
  exact h.1

theorem H074_six : IsCompletelyNormalB08 6 1 := by
  unfold IsCompletelyNormalB08
  decide

theorem H074_six_zero_not : ¬ IsCompletelyNormalB08 6 0 := by
  unfold IsCompletelyNormalB08
  decide

theorem H074_conv_saving (c c' : Cost) (n levels : Nat)
    (h : c.descent = c'.descent + h074Conv n levels)
    (h1 : c'.factorBase = c.factorBase) (h2 : c'.relations = c.relations)
    (h3 : c'.linearAlgebra = c.linearAlgebra) :
    c'.total ≤ c.total := by
  unfold Cost.total
  omega

def H074_claim : Prop :=
  ∀ (n levels v : Nat) (cBase cCN : Cost),
    (∃ d, 1 < d ∧ d < n ∧ n % d = 0) →
    IsCompletelyNormalB08 n v →
    cBase.descent = cCN.descent + h074Conv n levels →
    cCN.factorBase = cBase.factorBase → cCN.relations = cBase.relations →
    cCN.linearAlgebra = cBase.linearAlgebra →
    cCN.total ≤ cBase.total ∧ 100 * cBase.total ≤ 103 * cCN.total

/-! ## H075 -/

/-- **H075** — Hankel rank spectrum of the trace-component pencil and yield overdispersion.
Handbook 16.3.3.8 (Rank attacks), 16.3.3.9 (MinRank). Phase: cost-model.
Claim: `d x d` Hankel matrices over GF(2) have Daykin rank counts
(`1`, `3 * 4^(r-1)` for `0 < r < d`, `2^(2d-2)` for `r = d`), summing to `2^(2d-1)`;
decomposition counts per target are overdispersed relative to Poisson. -/
def h075Rows (d s : Nat) : List Nat :=
  (List.range d).map (fun i => (s >>> i) &&& (2 ^ d - 1))

def h075Count (d r : Nat) : Nat :=
  ((List.range (2 ^ (2 * d - 1))).filter (fun s => h074Rank (h075Rows d s) == r)).length

def h075Daykin (d r : Nat) : Nat :=
  if r = 0 then 1 else if r < d then 3 * 4 ^ (r - 1) else 2 ^ (2 * d - 2)

def h075Sum (f : Nat → Nat) : Nat → Nat
  | 0 => 0
  | k + 1 => h075Sum f k + f k

theorem H075_geom (k : Nat) : h075Sum (fun r => 3 * 4 ^ r) k + 1 = 4 ^ k := by
  induction k with
  | zero => simp [h075Sum]
  | succ k ih =>
    simp only [h075Sum]
    rw [Nat.pow_succ]
    omega

/-- The Daykin counts sum to `2^(2d-1)` (so the formula accounts for every Hankel matrix). -/
theorem H075_daykin_sum (d : Nat) (hd : 1 ≤ d) :
    h075Sum (h075Daykin d) (d + 1) = 2 ^ (2 * d - 1) := by
  obtain ⟨e, rfl⟩ : ∃ e, d = e + 1 := ⟨d - 1, by omega⟩
  have hmid : h075Sum (h075Daykin (e + 1)) (e + 1)
      = 1 + h075Sum (fun r => 3 * 4 ^ r) e := by
    have : ∀ k, k ≤ e → h075Sum (h075Daykin (e + 1)) (k + 1)
        = 1 + h075Sum (fun r => 3 * 4 ^ r) k := by
      intro k
      induction k with
      | zero => intro _; simp [h075Sum, h075Daykin]
      | succ k ih =>
        intro hk
        have := ih (by omega)
        simp only [h075Sum] at this ⊢
        have h2 : h075Daykin (e + 1) (k + 1) = 3 * 4 ^ k := by
          simp [h075Daykin]; omega
        omega
    exact this e (Nat.le_refl _)
  have hstep : ∀ (f : Nat → Nat) (k : Nat), h075Sum f (k + 1) = h075Sum f k + f k :=
    fun _ _ => rfl
  rw [hstep, hmid]
  have hg := H075_geom e
  have h2 : h075Daykin (e + 1) (e + 1) = 2 ^ (2 * e) := by
    have : 2 * (e + 1) - 2 = 2 * e := by omega
    simp [h075Daykin, this]
  rw [h2]
  have h4 : (4 : Nat) ^ e = 2 ^ (2 * e) := by
    rw [Nat.pow_mul]
  have h5 : 2 ^ (2 * (e + 1) - 1) = 2 * 2 ^ (2 * e) := by
    have : 2 * (e + 1) - 1 = 2 * e + 1 := by omega
    rw [this, Nat.pow_succ]; omega
  omega

theorem H075_count_zero_two : h075Count 2 0 = 1 := by decide

theorem H075_hist_two :
    (List.range 3).map (h075Count 2) = (List.range 3).map (h075Daykin 2) := by decide

theorem H075_hist_three :
    (List.range 4).map (h075Count 3) = (List.range 4).map (h075Daykin 3) := by decide

/-- Overdispersion in integers: `N * Σc² > (Σc)² + N * Σc` is `Var > Mean`. -/
def h075Over (N : Nat) (cnt : Nat → Nat) : Prop :=
  (h075Sum cnt N) ^ 2 + N * h075Sum cnt N < N * h075Sum (fun t => cnt t ^ 2) N

def H075_claim : Prop :=
  (∀ d, 1 ≤ d → ∀ r, r ≤ d → h075Count d r = h075Daykin d r) ∧
  (∀ (n : Nat) (cnt : Nat → Nat) (isDecompCount : Prop),
    isDecompCount → 17 ≤ n → n ≤ 21 → h075Over (2 ^ n) cnt)

/-! ## H076 -/

/-- **H076** — Batch-target marginal cost: left-kernel growth about 0.75 per extra relation.
Handbook 15.5.1 (Tornado codes), 15.3 (LDPC rank above ML threshold).
Phase: cost-model. Claim: above the orientability threshold the left-kernel
dimension grows with slope 0.70-0.78 per extra relation, and `k` targets need
about `c3 * B + 2k` relations instead of `k` separate solves. The algebraic step
used: `k` dependencies with unit determinant `D` determine the target logs
(here `k = 2`, adjugate). -/
def h076Batch (c3B k : Nat) : Nat := c3B + 2 * k

def h076Separate (c3B k : Nat) : Nat := k * (c3B + 2)

theorem H076_batch_le_separate (c3B k : Nat) (hk : 1 ≤ k) :
    h076Batch c3B k ≤ h076Separate c3B k := by
  unfold h076Batch h076Separate
  rw [Nat.mul_add]
  have : c3B ≤ k * c3B := Nat.le_mul_of_pos_left c3B hk
  omega

theorem H076_k64 : h076Batch 1840 64 < h076Separate 1840 64 := by decide

/-- Adjugate solve for two dependencies: `A t = r` with `D = a d - b c`. -/
theorem H076_adjugate (a b c d r1 r2 t1 t2 : Int)
    (e1 : a * t1 + b * t2 = r1) (e2 : c * t1 + d * t2 = r2) :
    (a * d - b * c) * t1 = d * r1 - b * r2 ∧ (a * d - b * c) * t2 = a * r2 - c * r1 := by
  subst e1 e2
  constructor <;> grind

/-- Uniqueness: two solutions of the same system agree when `D ≠ 0`. -/
theorem H076_unique (a b c d r1 r2 t1 t2 s1 s2 : Int) (hD : a * d - b * c ≠ 0)
    (e1 : a * t1 + b * t2 = r1) (e2 : c * t1 + d * t2 = r2)
    (f1 : a * s1 + b * s2 = r1) (f2 : c * s1 + d * s2 = r2) :
    t1 = s1 ∧ t2 = s2 := by
  have h1 := H076_adjugate a b c d r1 r2 t1 t2 e1 e2
  have h2 := H076_adjugate a b c d r1 r2 s1 s2 f1 f2
  constructor
  · exact Int.eq_of_mul_eq_mul_left hD (h1.1.trans h2.1.symm)
  · exact Int.eq_of_mul_eq_mul_left hD (h1.2.trans h2.2.symm)

def H076_claim : Prop :=
  ∀ (B : Nat) (kerDim : Nat → Nat),
    (∀ N1 N2, N1 ≤ N2 → 100 * N1 ≥ 92 * B → N2 ≤ B →
      70 * (N2 - N1) + 100 * kerDim N1 ≤ 100 * kerDim N2 ∧
      100 * kerDim N2 ≤ 78 * (N2 - N1) + 100 * kerDim N1) ∧
    (∀ k, 1 ≤ k → h076Batch (kerDim B) k ≤ h076Separate (kerDim B) k)

/-! ## H077 -/

/-- **H077** — Strength-2 covering array screening of the autolab configuration space.
Handbook 14.7.4 (Covering arrays). Phase: cost-model. Claim: a 6-run binary
strength-2 covering array plus a pairwise model finds a configuration within 10%
of the exhaustive best on at least 80% of toy curves using under 5% of the 128 runs. -/
def h077Cols : Fin 7 → List (Fin 6)
  | 0 => [0, 1, 2]
  | 1 => [0, 1, 3]
  | 2 => [0, 1, 4]
  | 3 => [0, 1, 5]
  | 4 => [0, 2, 3]
  | 5 => [0, 2, 4]
  | 6 => [0, 2, 5]

def h077Arr (r : Fin 6) (c : Fin 7) : Bool := decide (r ∈ h077Cols c)

theorem H077_covers :
    ∀ c1 c2 : Fin 7, c1 ≠ c2 → ∀ u v : Bool, ∃ r : Fin 6, h077Arr r c1 = u ∧ h077Arr r c2 = v := by
  decide

theorem H077_main_effects : ∀ c : Fin 7, ∀ u : Bool, ∃ r : Fin 6, h077Arr r c = u := by
  decide

theorem H077_budget : 6 * 100 < 5 * 128 := by decide

abbrev H077Cfg := Fin 7 → Bool

def h077Row (r : Fin 6) : H077Cfg := fun c => h077Arr r c

def h077Within10 (found best : Nat) : Bool := decide (10 * found ≤ 11 * best)

def H077_claim : Prop :=
  ∀ (curves : List (H077Cfg → Nat)) (best : (H077Cfg → Nat) → Nat)
    (pick : (H077Cfg → Nat) → H077Cfg),
    (∀ f c, best f ≤ f c) → (∀ f, ∃ c, f c = best f) →
    (∀ f g, (∀ r, f (h077Row r) = g (h077Row r)) → pick f = pick g) →
    5 * (curves.filter (fun f => h077Within10 (f (pick f)) (best f))).length
      ≥ 4 * curves.length

/-! ## H078 -/

/-- **H078** — Sidon-defect of Carlitz-torsion and spread-element factor bases.
Handbook 14.5.3, 14.4.4, 13.5.5, 14.3.3. Phase: cost-model. Claim: the number
of distinct pair sums of a base `V` of size `B` is at most `B(B+1)/2`, with
equality exactly when pair sums are injective (Sidon); the Carlitz-torsion
family is predicted to deviate from Poisson coverage by at least 1%. -/
def h078Pairs {α : Type} (add : α → α → α) : List α → List α
  | [] => []
  | a :: as => (a :: as).map (add a) ++ h078Pairs add as

def h078Tri : Nat → Nat
  | 0 => 0
  | n + 1 => h078Tri n + (n + 1)

def h078Distinct {α : Type} [DecidableEq α] : List α → Nat
  | [] => 0
  | a :: as => (if a ∈ as then 0 else 1) + h078Distinct as

theorem H078_pairs_length {α : Type} (add : α → α → α) (V : List α) :
    (h078Pairs add V).length = h078Tri V.length := by
  induction V with
  | nil => simp [h078Pairs, h078Tri]
  | cons a as ih =>
    simp only [h078Pairs, List.length_append, List.length_map, List.length_cons, h078Tri, ih]
    omega

theorem H078_distinct_le {α : Type} [DecidableEq α] (xs : List α) :
    h078Distinct xs ≤ xs.length := by
  induction xs with
  | nil => simp [h078Distinct]
  | cons a as ih =>
    simp only [h078Distinct, List.length_cons]
    split <;> omega

theorem H078_distinct_eq_iff {α : Type} [DecidableEq α] (xs : List α) :
    h078Distinct xs = xs.length ↔ xs.Nodup := by
  induction xs with
  | nil => simp [h078Distinct]
  | cons a as ih =>
    have hle := H078_distinct_le as
    simp only [h078Distinct, List.length_cons, List.nodup_cons]
    by_cases h : a ∈ as
    · simp [h]; omega
    · simp [h]
      constructor
      · intro h1
        exact ih.mp (by omega)
      · intro h1
        have := ih.mpr h1
        omega

/-- Coverage of a base is at most `B(B+1)/2`, with equality iff pair sums are injective. -/
theorem H078_coverage_le {α : Type} [DecidableEq α] (add : α → α → α) (V : List α) :
    h078Distinct (h078Pairs add V) ≤ h078Tri V.length := by
  have := H078_distinct_le (h078Pairs add V)
  rw [H078_pairs_length] at this
  exact this

theorem H078_coverage_eq_iff {α : Type} [DecidableEq α] (add : α → α → α) (V : List α) :
    h078Distinct (h078Pairs add V) = h078Tri V.length ↔ (h078Pairs add V).Nodup := by
  rw [← H078_pairs_length add V]
  exact H078_distinct_eq_iff _

theorem H078_tri_two_mul (n : Nat) : 2 * h078Tri n = n * (n + 1) := by
  induction n with
  | zero => simp [h078Tri]
  | succ n ih =>
    simp only [h078Tri]
    rw [Nat.mul_add, ih]
    grind

theorem H078_sidon_example :
    h078Distinct (h078Pairs (· + ·) [1, 2, 5, 11]) = h078Tri 4 := by decide

def H078_claim : Prop :=
  ∀ (covMean expMean : Nat) (fromCarlitzTorsion : Prop),
    fromCarlitzTorsion →
    100 * (if covMean ≤ expMean then expMean - covMean else covMean - expMean) ≥ expMean

/-! ## H079 -/

/-- **H079** — Delayed-reduction PLE dense core moving the hybrid switch point.
Handbook 13.4.6.1, 13.4.1.2, 13.4.2.2. Phase: cost-model. Claim: with 2-3 limb
modulus, delayed reduction lowers the per-op dense constant, moves the optimal
dense core to at least 1.5x larger, and lowers total linear-algebra cost by at
least 15%. -/
def h079Hyb (sparse dense : Nat → Nat) (d c : Nat) : Nat := sparse c + d * dense c

def h079IsArgmin (sparse dense : Nat → Nat) (cands : List Nat) (d c : Nat) : Prop :=
  c ∈ cands ∧ ∀ c'' ∈ cands, h079Hyb sparse dense d c ≤ h079Hyb sparse dense d c''

theorem H079_mono_d (sparse dense : Nat → Nat) (d d' c : Nat) (h : d' ≤ d) :
    h079Hyb sparse dense d' c ≤ h079Hyb sparse dense d c := by
  unfold h079Hyb
  have := Nat.mul_le_mul_right (dense c) h
  omega

/-- Cheaper dense kernel: the new optimum costs no more than the old one. -/
theorem H079_cost_down (sparse dense : Nat → Nat) (cands : List Nat) (d d' c c' : Nat)
    (hd : d' ≤ d) (hc : c ∈ cands) (hc' : h079IsArgmin sparse dense cands d' c') :
    h079Hyb sparse dense d' c' ≤ h079Hyb sparse dense d c := by
  have h1 := hc'.2 c hc
  have h2 := H079_mono_d sparse dense d d' c hd
  omega

/-- Single crossing: with a strictly increasing dense cost, a strictly cheaper
per-op constant never moves the optimal core down. -/
theorem H079_argmin_up (sparse dense : Nat → Nat) (cands : List Nat) (d d' c c' : Nat)
    (hd : d' < d)
    (hmono : ∀ x ∈ cands, ∀ y ∈ cands, x < y → dense x < dense y)
    (hc : h079IsArgmin sparse dense cands d c)
    (hc' : h079IsArgmin sparse dense cands d' c') :
    c ≤ c' := by
  refine Nat.le_of_not_lt (fun hlt' => ?_)
  have hden := hmono c' hc'.1 c hc.1 hlt'
  have h1 := hc'.2 c hc.1
  have h2 := hc.2 c' hc'.1
  unfold h079Hyb at h1 h2
  obtain ⟨k, hk⟩ : ∃ k, d = d' + 1 + k := ⟨d - d' - 1, by omega⟩
  obtain ⟨m, hm⟩ : ∃ m, dense c = dense c' + 1 + m := ⟨dense c - dense c' - 1, by omega⟩
  rw [hk, hm] at h2
  rw [hm] at h1
  simp only [Nat.add_mul, Nat.mul_add, Nat.mul_one, Nat.one_mul] at h1 h2
  have : d' * dense c' + 0 ≤ d' * dense c' + 0 := Nat.le_refl _
  grind

def H079_claim : Prop :=
  ∀ (sparse dense dense' : Nat → Nat) (cands : List Nat) (d d' c c' : Nat),
    3 * d' ≤ 2 * d →
    h079IsArgmin sparse dense cands d c →
    h079IsArgmin sparse dense' cands d' c' →
    3 * c ≤ 2 * c' ∧
    100 * h079Hyb sparse dense' d' c' ≤ 85 * h079Hyb sparse dense d c

/-! ## H080 -/

/-- **H080** — Hamming-weight degree and mixed-volume predictor for F4 cost.
Handbook 11.5.2.1, 11.5.2.2. Phase: cost-model. Claim: the bit-degree
(popcount of exponents) predictor hits the F4 maximum degree within +-1 on at
least 85% of toy instances while the semi-regular bound hits at most 65%. -/
def h080Pop (n : Nat) : Nat :=
  if h : n = 0 then 0 else n % 2 + h080Pop (n / 2)
termination_by n
decreasing_by omega

theorem h080Pop_eq (n : Nat) : h080Pop n = n % 2 + h080Pop (n / 2) := by
  by_cases h : n = 0
  · subst h; simp [h080Pop]
  · rw [h080Pop]; simp [h]

theorem H080_pop_le (n : Nat) : h080Pop n ≤ n := by
  induction n using Nat.strongRecOn with
  | _ n ih =>
    by_cases h : n = 0
    · subst h; simp [h080Pop]
    · rw [h080Pop_eq n]
      have := ih (n / 2) (by omega)
      omega

theorem H080_pop_one : h080Pop 1 = 1 := by
  rw [h080Pop_eq]; simp [h080Pop]

/-- Popcount is subadditive: `popcount (a + b) ≤ popcount a + popcount b`. -/
theorem H080_pop_add : ∀ (s a b : Nat), a + b = s → h080Pop (a + b) ≤ h080Pop a + h080Pop b := by
  intro s
  induction s using Nat.strongRecOn with
  | _ s ih =>
    intro a b hs
    by_cases h0 : a + b = 0
    · have ha : a = 0 := by omega
      have hb : b = 0 := by omega
      subst ha; subst hb; simp [h080Pop]
    · have ea := h080Pop_eq a
      have eb := h080Pop_eq b
      have es := h080Pop_eq (a + b)
      have ih1 := ih (a / 2 + b / 2) (by omega) (a / 2) (b / 2) rfl
      by_cases hc : a % 2 = 1 ∧ b % 2 = 1
      · have hh : (a + b) / 2 = a / 2 + b / 2 + 1 := by omega
        have ih2 := ih (a / 2 + b / 2 + 1) (by omega) (a / 2 + b / 2) 1 rfl
        rw [hh] at es
        rw [H080_pop_one] at ih2
        omega
      · have hh : (a + b) / 2 = a / 2 + b / 2 := by omega
        rw [hh] at es
        omega

/-- Weight degree: sum of popcounts of the exponents. Total degree: sum of exponents. -/
def h080Weight : List Nat → Nat
  | [] => 0
  | e :: es => h080Pop e + h080Weight es

def h080Total : List Nat → Nat
  | [] => 0
  | e :: es => e + h080Total es

theorem H080_weight_le_total (es : List Nat) : h080Weight es ≤ h080Total es := by
  induction es with
  | nil => simp [h080Weight, h080Total]
  | cons e es ih =>
    simp only [h080Weight, h080Total]
    have := H080_pop_le e
    omega

/-- Multiplying monomials adds exponent vectors; the weight degree stays subadditive. -/
theorem H080_weight_mul : ∀ (e1 e2 : List Nat),
    h080Weight (List.zipWith (· + ·) e1 e2) ≤ h080Weight e1 + h080Weight e2
  | [], _ => by simp [h080Weight]
  | _ :: _, [] => by simp [h080Weight]
  | a :: as, b :: bs => by
      simp only [List.zipWith_cons_cons, h080Weight]
      have := H080_pop_add (a + b) a b rfl
      have := H080_weight_mul as bs
      omega

structure h080Sys where
  obs : Nat
  predWeight : Nat
  predSemi : Nat

def h080Hit (obs pred : Nat) : Bool := decide (obs ≤ pred + 1 ∧ pred ≤ obs + 1)

theorem H080_hits_le (xs : List h080Sys) (pr : h080Sys → Nat) :
    (xs.filter (fun s => h080Hit s.obs (pr s))).length ≤ xs.length :=
  List.length_filter_le _ _

def H080_claim : Prop :=
  ∀ (xs : List h080Sys) (fromWeilF4Runs : Prop),
    fromWeilF4Runs → xs.length = 100 →
    85 * xs.length ≤ 100 * (xs.filter (fun s => h080Hit s.obs s.predWeight)).length ∧
    100 * (xs.filter (fun s => h080Hit s.obs s.predSemi)).length ≤ 65 * xs.length

end HandbookIC.Ideas.B08

#print axioms HandbookIC.Ideas.B08.h071XorSum_xor
#print axioms HandbookIC.Ideas.B08.h071_and_xor
#print axioms HandbookIC.Ideas.B08.H071_affine_in_x2
#print axioms HandbookIC.Ideas.B08.H071_descent_bound
#print axioms HandbookIC.Ideas.B08.H071_cost_total
#print axioms HandbookIC.Ideas.B08.H072_monotone
#print axioms HandbookIC.Ideas.B08.H072_cost_total
#print axioms HandbookIC.Ideas.B08.H073_biased_le
#print axioms HandbookIC.Ideas.B08.H073_work_mono
#print axioms HandbookIC.Ideas.B08.H074_normal_of_cn
#print axioms HandbookIC.Ideas.B08.H074_nonzero_of_cn
#print axioms HandbookIC.Ideas.B08.H074_six
#print axioms HandbookIC.Ideas.B08.H074_six_zero_not
#print axioms HandbookIC.Ideas.B08.H074_conv_saving
#print axioms HandbookIC.Ideas.B08.H075_geom
#print axioms HandbookIC.Ideas.B08.H075_daykin_sum
#print axioms HandbookIC.Ideas.B08.H075_count_zero_two
#print axioms HandbookIC.Ideas.B08.H075_hist_two
#print axioms HandbookIC.Ideas.B08.H075_hist_three
#print axioms HandbookIC.Ideas.B08.H076_batch_le_separate
#print axioms HandbookIC.Ideas.B08.H076_k64
#print axioms HandbookIC.Ideas.B08.H076_adjugate
#print axioms HandbookIC.Ideas.B08.H076_unique
#print axioms HandbookIC.Ideas.B08.H077_covers
#print axioms HandbookIC.Ideas.B08.H077_main_effects
#print axioms HandbookIC.Ideas.B08.H077_budget
#print axioms HandbookIC.Ideas.B08.H078_pairs_length
#print axioms HandbookIC.Ideas.B08.H078_distinct_le
#print axioms HandbookIC.Ideas.B08.H078_distinct_eq_iff
#print axioms HandbookIC.Ideas.B08.H078_coverage_le
#print axioms HandbookIC.Ideas.B08.H078_coverage_eq_iff
#print axioms HandbookIC.Ideas.B08.H078_tri_two_mul
#print axioms HandbookIC.Ideas.B08.H078_sidon_example
#print axioms HandbookIC.Ideas.B08.H079_mono_d
#print axioms HandbookIC.Ideas.B08.H079_cost_down
#print axioms HandbookIC.Ideas.B08.H079_argmin_up
#print axioms HandbookIC.Ideas.B08.h080Pop_eq
#print axioms HandbookIC.Ideas.B08.H080_pop_le
#print axioms HandbookIC.Ideas.B08.H080_pop_one
#print axioms HandbookIC.Ideas.B08.H080_pop_add
#print axioms HandbookIC.Ideas.B08.H080_weight_le_total
#print axioms HandbookIC.Ideas.B08.H080_weight_mul
#print axioms HandbookIC.Ideas.B08.H080_hits_le
