import HandbookIC.Core

/-!
# HandbookIC.Ideas.B06 — handbook ideas H051 .. H060
(relation collection H051-H055, relation filtering H056-H060)

Each idea has: a doc comment, definitions prefixed by the lower-case id,
`def Hxxx_claim : Prop` (all hypotheses explicit; curve/field facts are
hypotheses or record fields, nothing is postulated) and at least one proved
supporting theorem.  Empirical rates (rank growth, core fractions, speed-ups)
are never proved here; only the arithmetic and structure a real experiment
relies on.
-/

namespace HandbookIC.Ideas.B06

open HandbookIC

/-! ## Shared helpers: sparse linear systems, peeling, column permutations -/

/-- A sparse relation row: `Σ coef · x col ≡ rhs (mod m)`. -/
structure SRow where
  terms : List (Nat × Int)
  rhs : Int
  deriving DecidableEq

/-- Value of the left-hand side of a sparse row at an assignment `x`. -/
def b06TermSum (x : Nat → Int) (ts : List (Nat × Int)) : Int :=
  (ts.map (fun t => t.2 * x t.1)).sum

/-- Row `r` holds at `x` modulo `m` (`m = 0` is exact integer arithmetic). -/
def b06Holds (m : Int) (x : Nat → Int) (r : SRow) : Prop :=
  (b06TermSum x r.terms) % m = r.rhs % m

/-- `x` solves every row. -/
def b06Sat (m : Int) (x : Nat → Int) (rows : List SRow) : Prop :=
  ∀ r ∈ rows, b06Holds m x r

/-- The system has a solution. -/
def b06Solvable (m : Int) (rows : List SRow) : Prop :=
  ∃ x, b06Sat m x rows

/-- Left-hand sides depend only on the columns that occur. -/
theorem b06_termSum_congr (x y : Nat → Int) (ts : List (Nat × Int))
    (h : ∀ t ∈ ts, x t.1 = y t.1) : b06TermSum x ts = b06TermSum y ts := by
  unfold b06TermSum
  congr 1
  apply List.map_congr_left
  intro t ht
  rw [h t ht]

/-- Singleton (unit-coefficient) peeling preserves solvability: a row that is the
only one containing column `c`, with coefficient `1`, can be removed together
with `c`; any solution of the rest extends by back-substitution. -/
theorem b06_peel_solvable (m : Int) (c : Nat) (rest : List (Nat × Int)) (rhs : Int)
    (others : List SRow)
    (hrest : ∀ t ∈ rest, t.1 ≠ c)
    (hothers : ∀ r ∈ others, ∀ t ∈ r.terms, t.1 ≠ c) :
    b06Solvable m ((⟨(c, 1) :: rest, rhs⟩ : SRow) :: others) ↔ b06Solvable m others := by
  constructor
  · rintro ⟨x, hx⟩
    exact ⟨x, fun r hr => hx r (List.mem_cons_of_mem _ hr)⟩
  · rintro ⟨x, hx⟩
    refine ⟨fun j => if j = c then rhs - b06TermSum x rest else x j, ?_⟩
    intro r hr
    rcases List.mem_cons.mp hr with h | h
    · subst h
      have e1 : b06TermSum (fun j => if j = c then rhs - b06TermSum x rest else x j) rest
          = b06TermSum x rest := by
        apply b06_termSum_congr
        intro t ht
        simp [hrest t ht]
      unfold b06Holds
      have e2 : b06TermSum (fun j => if j = c then rhs - b06TermSum x rest else x j)
            ((c, 1) :: rest) = rhs := by
        simp only [b06TermSum, List.map_cons, List.sum_cons, ite_true] at e1 ⊢
        rw [e1]
        omega
      show b06TermSum _ ((c, 1) :: rest) % m = rhs % m
      rw [e2]
    · have := hx r h
      unfold b06Holds at this ⊢
      have e : b06TermSum (fun j => if j = c then rhs - b06TermSum x rest else x j) r.terms
          = b06TermSum x r.terms := by
        apply b06_termSum_congr
        intro t ht
        simp [hothers r h t ht]
      rw [e]
      exact this

/-- Back-substitution is unique modulo `m`: any value of column `c` that satisfies
the peeled row (with the rest fixed) is congruent to `rhs - rest`. -/
theorem b06_backsub_unique (m : Int) (v s rhs : Int)
    (h : (1 * v + s) % m = rhs % m) : v % m = (rhs - s) % m := by
  have e : v = (1 * v + s) - s := by omega
  calc v % m = ((1 * v + s) - s) % m := by rw [← e]
    _ = ((1 * v + s) % m - s % m) % m := Int.sub_emod _ _ _
    _ = (rhs % m - s % m) % m := by rw [h]
    _ = (rhs - s) % m := (Int.sub_emod _ _ _).symm

/-- Removing one row from a list strictly shortens it: the termination measure of
any peeling loop. -/
theorem b06_erase_length_lt (rows : List SRow) (r : SRow) (h : r ∈ rows) :
    (rows.erase r).length < rows.length := by
  have h1 := List.length_erase_of_mem h
  have h2 := List.length_pos_of_mem h
  omega

/-- Relabelling the columns of a sparse row by `σ`. -/
def b06PermRow (σ : Nat → Nat) (r : SRow) : SRow :=
  ⟨r.terms.map (fun t => (σ t.1, t.2)), r.rhs⟩

theorem b06_termSum_perm (σ : Nat → Nat) (x : Nat → Int) (ts : List (Nat × Int)) :
    b06TermSum x (ts.map (fun t => (σ t.1, t.2))) = b06TermSum (fun j => x (σ j)) ts := by
  unfold b06TermSum
  simp [List.map_map, Function.comp_def]

/-- A column permutation (with a left inverse) leaves solvability invariant. -/
theorem b06_perm_solvable (m : Int) (σ τ : Nat → Nat) (hτ : ∀ j, τ (σ j) = j)
    (rows : List SRow) :
    b06Solvable m (rows.map (b06PermRow σ)) ↔ b06Solvable m rows := by
  have key : ∀ x, b06Sat m x (rows.map (b06PermRow σ)) ↔ b06Sat m (fun j => x (σ j)) rows := by
    intro x
    unfold b06Sat b06Holds
    constructor
    · intro h r hr
      have := h (b06PermRow σ r) (List.mem_map_of_mem hr)
      simpa [b06PermRow, b06_termSum_perm] using this
    · intro h r' hr'
      obtain ⟨r, hr, rfl⟩ := List.mem_map.mp hr'
      have := h r hr
      simpa [b06PermRow, b06_termSum_perm] using this
  constructor
  · rintro ⟨x, hx⟩
    exact ⟨fun j => x (σ j), (key x).mp hx⟩
  · rintro ⟨y, hy⟩
    refine ⟨fun j => y (τ j), (key _).mpr ?_⟩
    have : (fun j => (fun j => y (τ j)) (σ j)) = y := by
      funext j; simp [hτ]
    rw [this]; exact hy

/-- Dense-phase cost model: `d` columns, row weight `w`. -/
def b06LA (d w : Nat) : Nat := d * d * w

theorem b06_LA_mono {d d' : Nat} (w : Nat) (h : d' ≤ d) : b06LA d' w ≤ b06LA d w := by
  unfold b06LA
  exact Nat.mul_le_mul_right w (Nat.mul_le_mul h h)

/-- Maximum of a list of degrees. -/
def b06MaxDeg (l : List Nat) : Nat := l.foldl max 0

theorem b06_foldl_max_ge (l : List Nat) (a : Nat) : a ≤ l.foldl max a := by
  induction l generalizing a with
  | nil => simp
  | cons x l ih => simp only [List.foldl_cons]; exact Nat.le_trans (Nat.le_max_left a x) (ih _)

theorem b06_le_maxDeg (l : List Nat) : ∀ d ∈ l, d ≤ b06MaxDeg l := by
  unfold b06MaxDeg
  suffices h : ∀ (a : Nat), ∀ d ∈ l, d ≤ l.foldl max a from h 0
  induction l with
  | nil => intro a d hd; simp at hd
  | cons x l ih =>
    intro a d hd
    simp only [List.foldl_cons]
    rcases List.mem_cons.mp hd with rfl | h
    · exact Nat.le_trans (Nat.le_max_right a d) (b06_foldl_max_ge l _)
    · exact ih _ d h

/-! ## H051 -/

/-- **H051** — Low-discrepancy lattice sweeps over (a,b) at high saturation.
Handbook 10.4.5.5 Discrepancy, 10.4.5.2 Lattice test.  Phase: relation-collection.
Claim: a Korobov rank-1 lattice over (a,b) has fewer duplicate relations and faster
rank growth than iid when the relations needed are >= 10% of the effective space,
and no difference below 1% saturation. -/
def h051Dups {α : Type} [DecidableEq α] : List α → Nat
  | [] => 0
  | x :: xs => (if x ∈ xs then 1 else 0) + h051Dups xs

/-- Korobov rank-1 lattice point `i ↦ (i, g·i mod M)`. -/
def h051Korobov (M g i : Nat) : Nat × Nat := (i, g * i % M)

/-- A measured paired experiment record (iid arm vs lattice arm). -/
structure h051Exp where
  need : Nat
  space : Nat
  iidDups : Nat
  latDups : Nat
  relsIid : Nat
  relsLat : Nat

/-- Prediction at 20% saturation: lattice duplicates under 3% of the needed
relations and 5% fewer relations to full rank. -/
def h051Prediction (e : h051Exp) : Prop :=
  100 * e.latDups < 3 * e.need ∧ 100 * e.relsLat ≤ 95 * e.relsIid

def H051_claim : Prop :=
  (∀ M g : Nat, h051Dups ((List.range M).map (h051Korobov M g)) = 0) ∧
  (∀ e : h051Exp, 0 < e.need → 5 * e.need ≥ e.space → 10 * e.iidDups ≥ e.need →
      h051Prediction e)

theorem H051_dups_zero_of_nodup {α : Type} [DecidableEq α] (l : List α) (h : l.Nodup) :
    h051Dups l = 0 := by
  induction l with
  | nil => rfl
  | cons x xs ih =>
    rw [List.nodup_cons] at h
    simp [h051Dups, h.1, ih h.2]

/-- The Korobov sweep has pairwise distinct (a,b) points, so a deterministic
decomposition yields zero duplicate relations. -/
theorem H051_korobov_nodup (M g : Nat) :
    ((List.range M).map (h051Korobov M g)).Nodup := by
  exact List.Pairwise.map _ (fun a b hab h => hab (congrArg Prod.fst h)) List.nodup_range

theorem H051_korobov_dups_zero (M g : Nat) :
    h051Dups ((List.range M).map (h051Korobov M g)) = 0 :=
  H051_dups_zero_of_nodup _ (H051_korobov_nodup M g)

/-- The duplicate counter does count: a three-point iid sample with a repeat has one
duplicate, the lattice sample of 16 points none (instance check). -/
theorem H051_dups_instance :
    h051Dups [(1, 2), (1, 2), (3, 4)] = 1 ∧
    h051Dups ((List.range 16).map (h051Korobov 16 5)) = 0 := by
  decide

/-! ## H052 -/

/-- **H052** — Multiplier-closed table via commuting x-only maps (Dickson analogue).
Handbook 9.6.1 Dickson polynomials basics, 9.6.2.2 Maps Phi_a, Psi_a.  Phase:
relation-collection.  Claim: a table `{x(kF_j) : k ∈ K}` raises relations per tuple by
about `|K|` without enlarging the matrix; cost `K·B + N/K` has optimum `2·sqrt(N·B)`. -/
def h052Coeff (ents : List (Int × Int)) : Int :=
  (ents.map (fun e => e.1 * e.2)).sum

/-- Contribution of table entries `(k, c)` over one base element with log `L`. -/
def h052Contribution (ents : List (Int × Int)) (L : Int) : Int :=
  (ents.map (fun e => e.2 * (e.1 * L))).sum

/-- Table cost `K·B` plus `M ≈ N/K` tuple trials. -/
def h052TableCost (K B M : Nat) : Nat := K * B + M

def H052_claim : Prop :=
  (∀ (ents : List (Int × Int)) (L : Int), h052Contribution ents L = h052Coeff ents * L) ∧
  (∀ K B N M : Nat, N ≤ K * M → 4 * N * B ≤ (h052TableCost K B M) ^ 2)

/-- `relation_scale`: a relation over table entries `k·F` with multiplicities `c`
is a relation over `F` with coefficient `Σ k·c`. -/
theorem H052_relation_scale (ents : List (Int × Int)) (L : Int) :
    h052Contribution ents L = h052Coeff ents * L := by
  induction ents with
  | nil => simp [h052Contribution, h052Coeff]
  | cons e es ih =>
    simp only [h052Contribution, h052Coeff, List.map_cons, List.sum_cons] at ih ⊢
    rw [ih]
    grind

theorem H052_four_le_sq (x y : Nat) : 4 * x * y ≤ (x + y) ^ 2 := by
  rcases Nat.le_total x y with h | h
  · obtain ⟨d, rfl⟩ := Nat.exists_eq_add_of_le h
    grind
  · obtain ⟨d, rfl⟩ := Nat.exists_eq_add_of_le h
    grind

/-- `(K·B + M)^2 ≥ 4·N·B` whenever `K·M ≥ N`: no `K` beats `2·sqrt(N·B)`. -/
theorem H052_cost_lower_bound (K B N M : Nat) (h : N ≤ K * M) :
    4 * N * B ≤ (h052TableCost K B M) ^ 2 := by
  unfold h052TableCost
  have h1 : 4 * N * B ≤ 4 * (K * M) * B := Nat.mul_le_mul_right B (Nat.mul_le_mul_left 4 h)
  have h2 := H052_four_le_sq (K * B) M
  have h3 : 4 * (K * M) * B = 4 * (K * B) * M := by grind
  omega

theorem H052_claim_holds : H052_claim :=
  ⟨H052_relation_scale, H052_cost_lower_bound⟩

/-! ## H053 -/

/-- **H053** — Consecutive-scalar sampling with pseudorandomness (C_2) guard.
Handbook 6.3.5.2 Measures of pseudorandomness, 6.3.5 Incomplete character sums.
Phase: relation-collection.  Claim: scanning `k, k+1, ...` with `R_{k+1} = R_k + P`
has the hit rate of independent scalars at one addition per candidate instead of a
scalar multiplication. -/
def h053Cost (cands unit : Nat) : Nat := cands * unit

/-- Under equal hit rates (same `p` hits per `t` candidates) the sequential arm
needs the same number of candidates as the independent one; costs differ by the
unit operation. -/
def H053_claim : Prop :=
  ∀ (need p t add mul : Nat) (c c' : Cost),
    add < mul → 0 < expectedTrials need p t →
    c.relations = h053Cost (expectedTrials need p t) mul →
    c'.relations = h053Cost (expectedTrials need p t) add →
    c'.factorBase = c.factorBase → c'.linearAlgebra = c.linearAlgebra →
    c'.descent = c.descent → c'.total < c.total

theorem H053_seq_le_indep (cands add mul : Nat) (h : add ≤ mul) :
    h053Cost cands add ≤ h053Cost cands mul :=
  Nat.mul_le_mul_left cands h

theorem H053_seq_lt_indep (cands add mul : Nat) (h : add < mul) (hc : 0 < cands) :
    h053Cost cands add < h053Cost cands mul :=
  Nat.mul_lt_mul_of_pos_left h hc

/-- A `k`-fold cheaper candidate step gives a `k`-fold cheaper relation phase. -/
theorem H053_speedup (cands add mul k : Nat) (h : k * add ≤ mul) :
    k * h053Cost cands add ≤ h053Cost cands mul := by
  unfold h053Cost
  calc k * (cands * add) = cands * (k * add) := by grind
    _ ≤ cands * mul := Nat.mul_le_mul_left cands h

theorem H053_claim_holds : H053_claim := by
  intro need p t add mul c c' hlt hpos hc hc' hf hl hd
  have h := H053_seq_lt_indep _ _ _ hlt hpos
  unfold Cost.total
  rw [hc', hc] at *
  omega

/-! ## H054 -/

/-- **H054** — Cubic/sextic Jacobi-sum j=0 panels with mu_3/mu_6 factor-base quotient.
Handbook 6.1.2 Jacobi and Gauss sums of small orders.  Phase: relation-collection.
Claim: on j=0 toys, quotienting by mu_3 on top of negation (the log is lifted by
`λ` with `λ^2+λ+1 = 0`) cuts the factor-base columns by 3 and keeps relations
correct by rewriting through `λ`. -/
def h054Cols (B : Nat) : Nat := orbitRepresentatives B 3

def H054_claim : Prop :=
  ∀ (n lam : Int) (B : Nat), lam * lam * lam % n = 1 % n → B % 3 = 0 →
    h054Cols B * 3 = B ∧
    (∀ l : Int, lam * (lam * (lam * l)) % n = l % n) ∧
    (∀ a l c : Int, a % n = (lam * l) % n → (c * a) % n = ((c * lam) * l) % n)

theorem H054_cols_exact (B : Nat) (h : B % 3 = 0) : h054Cols B * 3 = B := by
  unfold h054Cols orbitRepresentatives
  exact Nat.div_mul_cancel (Nat.dvd_of_mod_eq_zero h)

/-- The cube of the lifting multiplier acts trivially on logarithms. -/
theorem H054_cube_action (n lam : Int) (h : lam * lam * lam % n = 1 % n) (l : Int) :
    lam * (lam * (lam * l)) % n = l % n := by
  have e : lam * (lam * (lam * l)) = (lam * lam * lam) * l := by grind
  rw [e, Int.mul_emod, h, ← Int.mul_emod]
  simp

/-- Rewriting a relation term through the lift `log P' = λ log P`. -/
theorem H054_rewrite (n lam : Int) (a l c : Int) (h : a % n = (lam * l) % n) :
    (c * a) % n = ((c * lam) * l) % n := by
  rw [Int.mul_emod, h, ← Int.mul_emod, Int.mul_assoc]

/-- The dense phase on `B/3` columns costs at most a ninth. -/
theorem H054_la_ninth (B w : Nat) :
    9 * b06LA (h054Cols B) w ≤ b06LA B w := by
  have h := orbitRepresentatives_mul_le B 3
  unfold h054Cols b06LA
  generalize orbitRepresentatives B 3 = x at h ⊢
  have h2 := Nat.mul_le_mul h h
  have h3 : 9 * (x * x) ≤ B * B := by grind
  have h4 := Nat.mul_le_mul_right w h3
  grind

theorem H054_claim_holds : H054_claim := by
  intro n lam B h hB
  exact ⟨H054_cols_exact B hB, H054_cube_action n lam h, H054_rewrite n lam⟩

/-! ## H055 -/

/-- **H055** — Gray-code incremental products over a subspace factor base.
Handbook 5.3.5 Fast arithmetic using normal bases.  Phase: relation-collection.
Claim: enumerating `x1 ∈ V` in Gray order updates `p = x1·x2`, `s = x1+x2` by XOR,
cutting inner-loop multiplications from about 5 to 4 per pair, with the same
relation list. -/
def h055Gray (i : Nat) : Nat := i ^^^ (i >>> 1)

/-- Direct sequence `s_0 = x0`, `s_{i+1} = s_i xor b_i`. -/
def h055Seq (x0 : Nat) (b : Nat → Nat) : Nat → Nat
  | 0 => x0
  | i + 1 => h055Seq x0 b i ^^^ b i

/-- Incremental product `P_0 = f x0`, `P_{i+1} = P_i xor f(b_i)`. -/
def h055Inc (f : Nat → Nat) (x0 : Nat) (b : Nat → Nat) : Nat → Nat
  | 0 => f x0
  | i + 1 => h055Inc f x0 b i ^^^ f (b i)

/-- Multiplications per pair: direct `5`, Gray `4`. -/
def h055Mults (perPair pairs : Nat) : Nat := perPair * pairs

def H055_claim : Prop :=
  (∀ (f : Nat → Nat) (x0 : Nat) (b : Nat → Nat),
      (∀ x y, f (x ^^^ y) = f x ^^^ f y) →
      ∀ i, h055Inc f x0 b i = f (h055Seq x0 b i)) ∧
  (∀ pairs, 10 * (h055Mults 5 pairs - h055Mults 4 pairs) ≥ h055Mults 5 pairs)

/-- For a linear (XOR-additive) `f`, the incremental update equals the direct image. -/
theorem H055_incremental_eq (f : Nat → Nat) (x0 : Nat) (b : Nat → Nat)
    (hf : ∀ x y, f (x ^^^ y) = f x ^^^ f y) (i : Nat) :
    h055Inc f x0 b i = f (h055Seq x0 b i) := by
  induction i with
  | zero => rfl
  | succ i ih => simp only [h055Inc, h055Seq, ih, hf]

theorem H055_mult_saving (pairs : Nat) :
    10 * (h055Mults 5 pairs - h055Mults 4 pairs) ≥ h055Mults 5 pairs := by
  unfold h055Mults
  omega

/-- Instance check: the Gray code visits all 16 values of a 4-bit subspace once. -/
theorem H055_gray_visits_once_m4 : ((List.range 16).map h055Gray).Nodup := by
  decide

/-- Consecutive Gray codewords differ in exactly one bit (m = 4 instance). -/
theorem H055_gray_single_flip_m4 :
    ∀ i < 15, ∃ k < 4, h055Gray (i + 1) ^^^ h055Gray i = 2 ^ k := by
  decide

theorem H055_claim_holds : H055_claim :=
  ⟨H055_incremental_eq, H055_mult_saving⟩

/-! ## H056 -/

/-- **H056** — Overlap-bounded degree-balanced relation selection before filtering.
Handbook 17.3.5 Sequences with small Hamming correlation.  Phase: relation-filtering.
Claim: at fixed `B`, RS-profile greedy selection needs >= 5% fewer relations for full
column rank than uniform subsampling of the same pool. -/
def h056Dot {B : Nat} (row : Fin B → Int) (v : Fin B → Int) : Int :=
  finSum B (fun j => row j * v j)

/-- Unit vector at column `c`. -/
def h056Unit {B : Nat} (c : Fin B) : Fin B → Int := fun j => if j = c then 1 else 0

/-- Number of codewords `(a,b)` of the degree-<2 Reed-Solomon code over `Z/q` with
symbol `s` at position `x`. -/
def h056Cover (q x s : Nat) : Nat :=
  (((List.range q).flatMap (fun a => (List.range q).map (fun b => (a, b)))).filter
    (fun ab => (ab.1 + ab.2 * x) % q == s)).length

/-- Positions where two codewords agree. -/
def h056Agree (q : Nat) (u v : Nat × Nat) : Nat :=
  ((List.range q).filter (fun x => (u.1 + u.2 * x) % q == (v.1 + v.2 * x) % q)).length

def H056_claim : Prop :=
  (∀ (B : Nat) (rows : List (Fin B → Int)) (c : Fin B),
      (∀ r ∈ rows, r c = 0) →
      (∃ v : Fin B → Int, v c = 1 ∧ ∀ r ∈ rows, h056Dot r v = 0)) ∧
  (∀ (N_uniform N_greedy : Nat), 100 * N_greedy ≤ 95 * N_uniform → N_greedy ≤ N_uniform)

theorem H056_finSum_zero (B : Nat) : finSum B (fun _ => 0) = 0 := by
  induction B with
  | zero => rfl
  | succ B ih => simp [finSum, ih]

theorem H056_finSum_single : ∀ (B : Nat) (c : Fin B) (v : Int),
    finSum B (fun j => if j = c then v else 0) = v := by
  intro B
  induction B with
  | zero => intro c; exact c.elim0
  | succ B ih =>
    intro c v
    by_cases hc : c = Fin.last B
    · subst hc
      have : (fun j : Fin B => if j.castSucc = Fin.last B then v else 0) = fun _ => 0 := by
        funext j
        have hne : j.castSucc ≠ Fin.last B := Fin.ne_of_lt (Fin.castSucc_lt_last j)
        simp [hne]
      simp only [finSum]
      rw [this, H056_finSum_zero]
      simp
    · obtain ⟨c', rfl⟩ := Fin.exists_castSucc_eq.mpr hc
      have h1 : (fun j : Fin B => if j.castSucc = c'.castSucc then v else 0)
          = fun j => if j = c' then v else 0 := by
        funext j
        simp [Fin.castSucc_inj]
      have h2 : (Fin.last B = c'.castSucc) = False := by
        apply eq_false
        intro h
        exact Fin.ne_of_lt (Fin.castSucc_lt_last c') h.symm
      simp only [finSum]
      rw [h1, ih]
      simp [h2]

theorem H056_dot_unit {B : Nat} (row : Fin B → Int) (c : Fin B) :
    h056Dot row (h056Unit c) = row c := by
  unfold h056Dot h056Unit
  have : (fun j => row j * (if j = c then (1 : Int) else 0))
      = fun j => if j = c then row c else 0 := by
    funext j
    by_cases h : j = c
    · subst h; simp
    · simp [h]
  rw [this, H056_finSum_single]

/-- A column covered by no selected relation gives the kernel vector `e_c`, so the
column rank is at most `B - 1`. -/
theorem H056_zero_coverage_kernel (B : Nat) (rows : List (Fin B → Int)) (c : Fin B)
    (h : ∀ r ∈ rows, r c = 0) :
    ∃ v : Fin B → Int, v c = 1 ∧ ∀ r ∈ rows, h056Dot r v = 0 := by
  refine ⟨h056Unit c, by simp [h056Unit], ?_⟩
  intro r hr
  rw [H056_dot_unit]
  exact h r hr

/-- RS design (q = 5, k = 2): every symbol appears `q^(k-1) = 5` times at every
position, and two distinct codewords agree in at most `k-1 = 1` position. -/
theorem H056_RS_design_q5 :
    (∀ x < 5, ∀ s < 5, h056Cover 5 x s = 5) := by
  decide

theorem H056_RS_overlap_q3 :
    let pts := (List.range 3).flatMap (fun a => (List.range 3).map (fun b => (a, b)))
    ∀ u ∈ pts, ∀ v ∈ pts, u ≠ v → h056Agree 3 u v ≤ 1 := by
  decide

theorem H056_claim_holds_fragment : (∀ (N_uniform N_greedy : Nat),
    100 * N_greedy ≤ 95 * N_uniform → N_greedy ≤ N_uniform) := by
  intro u g h
  omega

/-! ## H057 -/

/-- **H057** — Density-evolution threshold for filtering overhead (non-uniform degrees).
Handbook 16.3.3.12 Sparse linear solving, coding-theory cross-over.  Phase:
relation-filtering.  Claim: the core size after peeling matches the density-evolution
fixed point within 5%, so the dense-phase cost is predictable without running LA. -/
def h057Within (pct a b : Nat) : Prop := 100 * a ≤ (100 + pct) * b

def H057_claim : Prop :=
  ∀ (core pred w : Nat), h057Within 5 core pred →
    10000 * b06LA core w ≤ 11025 * b06LA pred w

/-- A 5% error in the predicted core is at most a 10.25% error in the quadratic
dense-phase cost. -/
theorem H057_cost_transfer (core pred w : Nat) (h : h057Within 5 core pred) :
    10000 * b06LA core w ≤ 11025 * b06LA pred w := by
  unfold h057Within at h
  unfold b06LA
  have h2 := Nat.mul_le_mul h h
  have h3 : 10000 * (core * core) ≤ 11025 * (pred * pred) := by grind
  have h4 := Nat.mul_le_mul_right w h3
  grind

theorem H057_claim_holds : H057_claim := fun core pred w h => H057_cost_transfer core pred w h

/-- Peeling a unit singleton column preserves solvability and shortens the system. -/
theorem H057_peel_sound (m : Int) (c : Nat) (rest : List (Nat × Int)) (rhs : Int)
    (others : List SRow) (hrest : ∀ t ∈ rest, t.1 ≠ c)
    (hothers : ∀ r ∈ others, ∀ t ∈ r.terms, t.1 ≠ c) :
    (b06Solvable m ((⟨(c, 1) :: rest, rhs⟩ : SRow) :: others) ↔ b06Solvable m others) ∧
    others.length < ((⟨(c, 1) :: rest, rhs⟩ : SRow) :: others).length :=
  ⟨b06_peel_solvable m c rest rhs others hrest hothers, by simp⟩

/-! ## H058 -/

/-- **H058** — Closed-form 2-core as a hidden-structure diagnostic.
Handbook 15.5.2 LT and fountain codes, 15.5.3 Raptor codes.  Phase: relation-filtering.
Claim: the post-peeling core fraction equals density evolution within 3 points;
deficits measure engineerable structure, excess measures hidden bias. -/
inductive h058Verdict
  | deficit | onFormula | excess
  deriving DecidableEq

/-- Classify a measured core (in thousandths of `B`) against the formula with tolerance
`tol` thousandths. -/
def h058Classify (tol meas formula : Nat) : h058Verdict :=
  if meas + tol < formula then .deficit
  else if formula + tol < meas then .excess
  else .onFormula

def H058_claim : Prop :=
  ∀ (B core f w : Nat), 100 * core ≤ f * B → f ≤ 100 →
    core ≤ B ∧ b06LA core w ≤ b06LA B w

theorem H058_core_le (B core f : Nat) (h : 100 * core ≤ f * B) (hf : f ≤ 100) :
    core ≤ B := by
  have h1 : f * B ≤ 100 * B := Nat.mul_le_mul_right B hf
  omega

theorem H058_claim_holds : H058_claim := by
  intro B core f w h hf
  have hc := H058_core_le B core f h hf
  exact ⟨hc, b06_LA_mono w hc⟩

/-- The classifier is exhaustive and sound for the two off-formula outcomes. -/
theorem H058_classify_sound (tol meas formula : Nat) :
    (h058Classify tol meas formula = .deficit → meas + tol < formula) ∧
    (h058Classify tol meas formula = .excess → formula + tol < meas) ∧
    (h058Classify tol meas formula = .onFormula →
        formula ≤ meas + tol ∧ meas ≤ formula + tol) := by
  unfold h058Classify
  by_cases h1 : meas + tol < formula
  · simp [h1]
  · by_cases h2 : formula + tol < meas
    · simp [h1, h2]
    · simp [h1, h2]; omega

/-- Instance: 0.72 vs 0.85 with tolerance 0.03 are different verdicts. -/
theorem H058_classify_instance :
    h058Classify 30 720 850 = .deficit ∧ h058Classify 30 720 700 = .onFormula ∧
    h058Classify 30 800 700 = .excess := by
  decide

/-- Peeling preserves kernel solvability (restated for the diagnostic). -/
theorem H058_peel_preserves (m : Int) (c : Nat) (rest : List (Nat × Int)) (rhs : Int)
    (others : List SRow) (hrest : ∀ t ∈ rest, t.1 ≠ c)
    (hothers : ∀ r ∈ others, ∀ t ∈ r.terms, t.1 ≠ c) :
    b06Solvable m ((⟨(c, 1) :: rest, rhs⟩ : SRow) :: others) ↔ b06Solvable m others :=
  b06_peel_solvable m c rest rhs others hrest hothers

/-! ## H059 -/

/-- **H059** — Closed-form peeling core with max-degree inactivation ordering.
Handbook 15.5 Raptor codes, 15.5.1 Tornado codes, 15.3 LDPC density evolution.
Phase: relation-filtering.  Claim: at `N = B` the core is `0.723 B`; peel plus
inactivation then Wiedemann on the core costs >= 1.5x fewer modmuls than on the
unfiltered matrix. -/
def H059_claim : Prop :=
  ∀ (B core w : Nat), 1000 * core ≤ 723 * B → 3 * b06LA core w ≤ 2 * b06LA B w

theorem H059_wiedemann_gain (B core w : Nat) (h : 1000 * core ≤ 723 * B) :
    3 * b06LA core w ≤ 2 * b06LA B w := by
  unfold b06LA
  have h2 := Nat.mul_le_mul h h
  have h3 : 3 * (core * core) ≤ 2 * (B * B) := by grind
  have h4 := Nat.mul_le_mul_right w h3
  grind

theorem H059_claim_holds : H059_claim := fun B core w h => H059_wiedemann_gain B core w h

/-- Peel-step invariance with unique back-substitution: the reduced system is solvable
iff the full one is, and the eliminated column is determined modulo `m`. -/
theorem H059_peel_backsub (m : Int) (c : Nat) (rest : List (Nat × Int)) (rhs : Int)
    (others : List SRow) (hrest : ∀ t ∈ rest, t.1 ≠ c)
    (hothers : ∀ r ∈ others, ∀ t ∈ r.terms, t.1 ≠ c) :
    (b06Solvable m ((⟨(c, 1) :: rest, rhs⟩ : SRow) :: others) ↔ b06Solvable m others) ∧
    (∀ x : Nat → Int, b06Holds m x ⟨(c, 1) :: rest, rhs⟩ →
        x c % m = (rhs - b06TermSum x rest) % m) := by
  refine ⟨b06_peel_solvable m c rest rhs others hrest hothers, ?_⟩
  intro x hx
  apply b06_backsub_unique
  unfold b06Holds at hx
  simpa [b06TermSum] using hx

/-- Inactivation picks a column of maximal residual weight. -/
theorem H059_inactivate_max (degs : List Nat) : ∀ d ∈ degs, d ≤ b06MaxDeg degs :=
  b06_le_maxDeg degs

/-! ## H060 -/

/-- **H060** — Inactivation-decoding order replacing greedy singleton/clique removal.
Handbook 14.4.6 k-Arcs and linear MDS codes.  Phase: relation-filtering.
Claim: inactivating the max-residual-weight column when peeling stalls leaves a dense
core >= 10% smaller than singleton-plus-clique filtering, lowering the dense cost; a
unit-coefficient peel preserves solution sets and inactivation is a column
permutation. -/
def H060_claim : Prop :=
  (∀ (dSC dIn : Nat), 10 * dIn ≤ 9 * dSC → 1000 * dIn ^ 3 ≤ 729 * dSC ^ 3) ∧
  (∀ (m : Int) (σ τ : Nat → Nat), (∀ j, τ (σ j) = j) → ∀ rows : List SRow,
      b06Solvable m (rows.map (b06PermRow σ)) ↔ b06Solvable m rows)

/-- A core at least 10% smaller cuts the cubic dense phase by at least 27%. -/
theorem H060_dense_cubic (dSC dIn : Nat) (h : 10 * dIn ≤ 9 * dSC) :
    1000 * dIn ^ 3 ≤ 729 * dSC ^ 3 := by
  have h1 := Nat.pow_le_pow_left h 3
  rw [Nat.mul_pow, Nat.mul_pow] at h1
  omega

/-- Inactivation is a column permutation: solution sets are invariant. -/
theorem H060_inactivation_perm (m : Int) (σ τ : Nat → Nat) (hτ : ∀ j, τ (σ j) = j)
    (rows : List SRow) :
    b06Solvable m (rows.map (b06PermRow σ)) ↔ b06Solvable m rows :=
  b06_perm_solvable m σ τ hτ rows

theorem H060_claim_holds : H060_claim :=
  ⟨H060_dense_cubic, H060_inactivation_perm⟩

/-- Single-column unit peel preserves solution sets modulo `l`. -/
theorem H060_unit_peel (l : Int) (c : Nat) (rest : List (Nat × Int)) (rhs : Int)
    (others : List SRow) (hrest : ∀ t ∈ rest, t.1 ≠ c)
    (hothers : ∀ r ∈ others, ∀ t ∈ r.terms, t.1 ≠ c) :
    b06Solvable l ((⟨(c, 1) :: rest, rhs⟩ : SRow) :: others) ↔ b06Solvable l others :=
  b06_peel_solvable l c rest rhs others hrest hothers

end HandbookIC.Ideas.B06

#print axioms HandbookIC.Ideas.B06.b06_termSum_congr
#print axioms HandbookIC.Ideas.B06.b06_peel_solvable
#print axioms HandbookIC.Ideas.B06.b06_backsub_unique
#print axioms HandbookIC.Ideas.B06.b06_erase_length_lt
#print axioms HandbookIC.Ideas.B06.b06_termSum_perm
#print axioms HandbookIC.Ideas.B06.b06_perm_solvable
#print axioms HandbookIC.Ideas.B06.b06_LA_mono
#print axioms HandbookIC.Ideas.B06.b06_foldl_max_ge
#print axioms HandbookIC.Ideas.B06.b06_le_maxDeg
#print axioms HandbookIC.Ideas.B06.H051_dups_zero_of_nodup
#print axioms HandbookIC.Ideas.B06.H051_korobov_nodup
#print axioms HandbookIC.Ideas.B06.H051_korobov_dups_zero
#print axioms HandbookIC.Ideas.B06.H051_dups_instance
#print axioms HandbookIC.Ideas.B06.H052_relation_scale
#print axioms HandbookIC.Ideas.B06.H052_four_le_sq
#print axioms HandbookIC.Ideas.B06.H052_cost_lower_bound
#print axioms HandbookIC.Ideas.B06.H052_claim_holds
#print axioms HandbookIC.Ideas.B06.H053_seq_le_indep
#print axioms HandbookIC.Ideas.B06.H053_seq_lt_indep
#print axioms HandbookIC.Ideas.B06.H053_speedup
#print axioms HandbookIC.Ideas.B06.H053_claim_holds
#print axioms HandbookIC.Ideas.B06.H054_cols_exact
#print axioms HandbookIC.Ideas.B06.H054_cube_action
#print axioms HandbookIC.Ideas.B06.H054_rewrite
#print axioms HandbookIC.Ideas.B06.H054_la_ninth
#print axioms HandbookIC.Ideas.B06.H054_claim_holds
#print axioms HandbookIC.Ideas.B06.H055_incremental_eq
#print axioms HandbookIC.Ideas.B06.H055_mult_saving
#print axioms HandbookIC.Ideas.B06.H055_gray_visits_once_m4
#print axioms HandbookIC.Ideas.B06.H055_gray_single_flip_m4
#print axioms HandbookIC.Ideas.B06.H055_claim_holds
#print axioms HandbookIC.Ideas.B06.H056_finSum_zero
#print axioms HandbookIC.Ideas.B06.H056_finSum_single
#print axioms HandbookIC.Ideas.B06.H056_dot_unit
#print axioms HandbookIC.Ideas.B06.H056_zero_coverage_kernel
#print axioms HandbookIC.Ideas.B06.H056_RS_design_q5
#print axioms HandbookIC.Ideas.B06.H056_RS_overlap_q3
#print axioms HandbookIC.Ideas.B06.H056_claim_holds_fragment
#print axioms HandbookIC.Ideas.B06.H057_cost_transfer
#print axioms HandbookIC.Ideas.B06.H057_claim_holds
#print axioms HandbookIC.Ideas.B06.H057_peel_sound
#print axioms HandbookIC.Ideas.B06.H058_core_le
#print axioms HandbookIC.Ideas.B06.H058_claim_holds
#print axioms HandbookIC.Ideas.B06.H058_classify_sound
#print axioms HandbookIC.Ideas.B06.H058_classify_instance
#print axioms HandbookIC.Ideas.B06.H058_peel_preserves
#print axioms HandbookIC.Ideas.B06.H059_wiedemann_gain
#print axioms HandbookIC.Ideas.B06.H059_claim_holds
#print axioms HandbookIC.Ideas.B06.H059_peel_backsub
#print axioms HandbookIC.Ideas.B06.H059_inactivate_max
#print axioms HandbookIC.Ideas.B06.H060_dense_cubic
#print axioms HandbookIC.Ideas.B06.H060_inactivation_perm
#print axioms HandbookIC.Ideas.B06.H060_claim_holds
#print axioms HandbookIC.Ideas.B06.H060_unit_peel
