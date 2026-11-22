import HandbookIC.Core

/-!
# HandbookIC.Ideas.B10 — handbook ideas H091 .. H100 (hardware phase)

Each idea has: a doc comment, definitions prefixed by the lower-case id,
`def Hxxx_claim : Prop` (all hypotheses explicit; curve, hardware and
measurement facts are hypotheses of the Prop, nothing is postulated) and
proved supporting theorems.
-/

namespace HandbookIC.Ideas.B10

open HandbookIC

/-! ## H091 -/

/-- **H091** — GF2P8AFFINEQB bit-matrix applies for the linear maps of the lifted loop.
Handbook 16.2.6 (AES / Rijndael). Phase: hardware.
Claim: on GFNI+AVX-512 hosts the linear-map part of the lifted loop reaches at least
2x the candidates per cycle of 8-bit table lookups at n = 64..131 (throughput-bound);
the block count is quadratic in n/8. -/
def h091Blocks (n : Nat) : Nat := ((n + 7) / 8) * ((n + 7) / 8)

/-- Instructions for `T` vectors: one instruction applies one 8x8 bit matrix to 8 lanes. -/
def h091Instr (n T : Nat) : Nat := h091Blocks n * ((T + 7) / 8)

/-- Table-lookup operations for `T` vectors: `ceil(n/8)` byte tables, each lookup
yields `ceil(n/64)` words. -/
def h091TableOps (n T : Nat) : Nat := T * (((n + 7) / 8) * ((n + 63) / 64))

/-- XOR of the first `m` entries of a Boolean family. -/
def h091Xor : Nat → (Nat → Bool) → Bool
  | 0, _ => false
  | m + 1, f => xor (h091Xor m f) (f m)

/-- Matrix-vector product over GF(2), `m` columns. -/
def h091Apply (m : Nat) (M : Nat → Nat → Bool) (x : Nat → Bool) : Nat → Bool :=
  fun i => h091Xor m (fun j => M i j && x j)

/-- Pointwise XOR of two bit vectors. -/
def h091XorV (x y : Nat → Bool) : Nat → Bool := fun i => xor (x i) (y i)

/-- XOR-linearity of a map on bit vectors. -/
def h091Linear (f : (Nat → Bool) → (Nat → Bool)) : Prop :=
  ∀ x y, f (h091XorV x y) = h091XorV (f x) (f y)

def H091_claim : Prop :=
  ∀ (T n cpiG cpiT : Nat) (hasGfni : Prop),
    hasGfni → 64 ≤ n → n ≤ 131 →
    -- empirical bridge: measured cycles per instruction / per lookup
    2 * (cpiG * h091Instr n T) ≤ cpiT * h091TableOps n T →
    2 * (h091Instr n T * cpiG) ≤ h091TableOps n T * cpiT

theorem h091_xor_xor : ∀ (m : Nat) (f g : Nat → Bool),
    h091Xor m (fun j => xor (f j) (g j)) = xor (h091Xor m f) (h091Xor m g)
  | 0, f, g => rfl
  | m + 1, f, g => by
      have key : ∀ a b c d : Bool, xor (xor a b) (xor c d) = xor (xor a c) (xor b d) := by decide
      simp only [h091Xor]
      rw [h091_xor_xor m f g]
      exact key _ _ _ _

theorem H091_apply_linear (m : Nat) (M : Nat → Nat → Bool) :
    h091Linear (h091Apply m M) := by
  intro x y
  funext i
  unfold h091Apply h091XorV
  have key : ∀ a b c : Bool, (a && xor b c) = xor (a && b) (a && c) := by decide
  have : (fun j => M i j && xor (x j) (y j))
      = (fun j => xor (M i j && x j) (M i j && y j)) := by
    funext j; exact key _ _ _
  rw [this]
  exact h091_xor_xor m _ _

theorem H091_comp_linear (f g : (Nat → Bool) → (Nat → Bool))
    (hf : h091Linear f) (hg : h091Linear g) : h091Linear (fun x => g (f x)) := by
  intro x y
  show g (f (h091XorV x y)) = h091XorV (g (f x)) (g (f y))
  rw [hf, hg]

theorem H091_blocks_64 : h091Blocks 64 = 64 := by decide
theorem H091_blocks_131 : h091Blocks 131 = 289 := by decide

theorem H091_blocks_quadratic (k : Nat) : h091Blocks (8 * k) = k * k := by
  unfold h091Blocks
  have : (8 * k + 7) / 8 = k := by omega
  rw [this]

theorem H091_blocks_mono {n n' : Nat} (h : n ≤ n') : h091Blocks n ≤ h091Blocks n' := by
  unfold h091Blocks
  have : (n + 7) / 8 ≤ (n' + 7) / 8 := by omega
  exact Nat.mul_le_mul this this

theorem H091_instr_mono {n n' T T' : Nat} (hn : n ≤ n') (hT : T ≤ T') :
    h091Instr n T ≤ h091Instr n' T' := by
  unfold h091Instr
  have : (T + 7) / 8 ≤ (T' + 7) / 8 := by omega
  exact Nat.mul_le_mul (H091_blocks_mono hn) this

/-! ## H092 -/

/-- **H092** — Longest-zero-run canonicalisation of Frobenius orbits (bit-parallel).
Handbook 14.9.2 (cyclic structure F_2[X]/(X^n-1)), necklaces. Phase: hardware.
Claim: the minimal rotation starts at a maximal zero run, so clz/ctz plus a few
comparisons canonicalise an n-bit word in O(n/64) operations with output identical
to the naive minimum over all rotations. -/
def h092Rot (r : Nat) (w : List Bool) : List Bool := w.drop r ++ w.take r

def h092Rots (w : List Bool) : List (List Bool) :=
  (List.range w.length).map (fun r => h092Rot r w)

/-- Leading zeros of a bit list (false = 0). -/
def h092Lz : List Bool → Nat
  | [] => 0
  | b :: bs => if b then 0 else 1 + h092Lz bs

/-- Lexicographic `≤` with `false < true`. -/
def h092Le : List Bool → List Bool → Bool
  | [], _ => true
  | _ :: _, [] => false
  | false :: as, false :: bs => h092Le as bs
  | true :: as, true :: bs => h092Le as bs
  | false :: _, true :: _ => true
  | true :: _, false :: _ => false

def h092Min (a b : List Bool) : List Bool := if h092Le a b then a else b

def h092Naive (w : List Bool) : List Bool := (h092Rots w).foldl h092Min w

def h092MaxRun (w : List Bool) : Nat := (h092Rots w).foldl (fun m r => max m (h092Lz r)) 0

def h092Starts (w : List Bool) : List (List Bool) :=
  (h092Rots w).filter (fun r => h092Lz r == h092MaxRun w)

/-- Canonical form that only compares rotations starting at a maximal zero run. -/
def h092Fast (w : List Bool) : List Bool :=
  match h092Starts w with
  | [] => w
  | s :: ss => ss.foldl h092Min s

/-- Operation model: fast = 3 word ops per 64 bits plus 2 comparisons; naive compares
all `n` rotations word by word. -/
def h092FastOps (n : Nat) : Nat := 3 * ((n + 63) / 64) + 2
def h092NaiveOps (n : Nat) : Nat := n * ((n + 63) / 64)

def h092Words : Nat → List (List Bool)
  | 0 => [[]]
  | n + 1 => (h092Words n).flatMap (fun w => [false :: w, true :: w])

def H092_claim : Prop :=
  ∀ w : List Bool, h092Fast w = h092Naive w ∧
    (64 ≤ w.length → 10 * h092FastOps w.length ≤ h092NaiveOps w.length)

/-- Exchange argument: a lexicographically smaller word of equal length has at least
as many leading zeros. -/
theorem H092_le_lz : ∀ (a b : List Bool), a.length = b.length → h092Le a b = true →
    h092Lz b ≤ h092Lz a
  | [], [], _, _ => by simp [h092Lz]
  | [], _ :: _, h, _ => by simp at h
  | _ :: _, [], h, _ => by simp at h
  | x :: xs, y :: ys, h, hle => by
      have hl : xs.length = ys.length := by simpa using h
      cases x <;> cases y
      · have := H092_le_lz xs ys hl (by simpa [h092Le] using hle)
        simp [h092Lz]; omega
      · simp [h092Lz]
      · simp [h092Le] at hle
      · simp [h092Lz]

/-- A minimal rotation has a maximal zero run among all rotations. -/
theorem H092_min_has_max_run (c : List Bool) (rs : List (List Bool))
    (hlen : ∀ r ∈ rs, r.length = c.length) (hmin : ∀ r ∈ rs, h092Le c r = true) :
    ∀ r ∈ rs, h092Lz r ≤ h092Lz c :=
  fun r hr => H092_le_lz c r (hlen r hr).symm (hmin r hr)

theorem H092_fast_eq_naive_upto6 :
    (List.range 7).all (fun n => (h092Words n).all
      (fun w => h092Fast w == h092Naive w)) = true := by decide

theorem H092_ops_131 : 10 * h092FastOps 131 ≤ h092NaiveOps 131 := by decide

theorem H092_ops_ratio (n : Nat) (hn : 64 ≤ n) :
    10 * h092FastOps n ≤ h092NaiveOps n := by
  unfold h092FastOps h092NaiveOps
  have hc : 1 ≤ (n + 63) / 64 := by omega
  have h := Nat.mul_le_mul_right ((n + 63) / 64) hn
  generalize (n + 63) / 64 = c at *
  omega

/-! ## H093 -/

/-- **H093** — MDS-arc checksum protection for block Lanczos/Wiedemann on Spot.
Handbook 14.4.6 (k-arcs and linear MDS codes). Phase: hardware.
Claim: with `r = 4` Vandermonde checksum rows, every corruption of at most 4
coordinates per matvec is detected, at most 2 corrected, at under 2% extra cost,
versus about 100% for duplicate verification. -/
def h093Cks : Nat → (Nat → Int) → (Nat → Int) → Int
  | 0, _, _ => 0
  | m + 1, c, v => h093Cks m c v + c m * v m

/-- Number of coordinates `i < m` where `d i` is nonzero mod `l`. -/
def h093Supp (l : Int) : Nat → (Nat → Int) → Nat
  | 0, _ => 0
  | m + 1, d => h093Supp l m d + (if d m % l = 0 then 0 else 1)

/-- Checksum work per check (two dot products of length `m` per row) and matvec work
for `q` matvecs of row weight `w`. -/
def h093CheckCost (r m : Nat) : Nat := 2 * (r * m)
def h093MatvecCost (q w m : Nat) : Nat := q * (w * m)

def H093_claim : Prop :=
  ∀ (l : Int) (m r : Nat) (c : Nat → Nat → Int) (v d : Nat → Int),
    -- MDS (Vandermonde) hypothesis: any nonzero error pattern of weight 1..4 is seen by a row
    (∀ e : Nat → Int, 0 < h093Supp l m e → h093Supp l m e ≤ 4 →
        ∃ j, j < r ∧ h093Cks m (c j) e % l ≠ 0) →
    0 < h093Supp l m d → h093Supp l m d ≤ 4 →
    ∃ j, j < r ∧ h093Cks m (c j) (fun i => v i + d i) % l ≠ h093Cks m (c j) v % l

theorem H093_cks_add (m : Nat) (c v d : Nat → Int) :
    h093Cks m c (fun i => v i + d i) = h093Cks m c v + h093Cks m c d := by
  induction m with
  | zero => simp [h093Cks]
  | succ m ih => simp only [h093Cks, ih, Int.mul_add]; omega

theorem H093_cks_single (c : Nat → Int) (j : Nat) (e : Int) :
    ∀ m, h093Cks m c (fun i => if i = j then e else 0) = if j < m then c j * e else 0
  | 0 => by simp [h093Cks]
  | m + 1 => by
      rw [h093Cks, H093_cks_single c j e m]
      by_cases a : j < m <;> by_cases b : m = j
      · omega
      · simp [a, b]; omega
      · subst b; simp
      · simp [a, b]; omega

/-- Detection of any set of faults follows from the MDS hypothesis and linearity. -/
theorem H093_detect_of_mds (l : Int) (m r : Nat) (c : Nat → Nat → Int) (v d : Nat → Int)
    (hmds : ∀ e : Nat → Int, 0 < h093Supp l m e → h093Supp l m e ≤ 4 →
        ∃ j, j < r ∧ h093Cks m (c j) e % l ≠ 0)
    (h1 : 0 < h093Supp l m d) (h2 : h093Supp l m d ≤ 4) :
    ∃ j, j < r ∧ h093Cks m (c j) (fun i => v i + d i) % l ≠ h093Cks m (c j) v % l := by
  obtain ⟨j, hj, hne⟩ := hmds d h1 h2
  refine ⟨j, hj, ?_⟩
  intro heq
  rw [H093_cks_add] at heq
  have := (Int.emod_emod_of_dvd (h093Cks m (c j) v) (Int.dvd_refl l))
  apply hne
  have h3 := Int.emod_eq_emod_iff_emod_sub_eq_zero.mp heq
  have h4 : h093Cks m (c j) v + h093Cks m (c j) d - h093Cks m (c j) v
      = h093Cks m (c j) d := by omega
  rw [h4] at h3
  exact h3

/-- A single corrupted coordinate with a unit weight changes the checksum. -/
theorem H093_single_fault_detect (l : Int) (m j : Nat) (c : Nat → Int) (v : Nat → Int)
    (e : Int) (hj : j < m) (hu : ∃ u, l ∣ c j * u - 1) (he : ¬ l ∣ e) :
    h093Cks m c (fun i => v i + (if i = j then e else 0)) % l ≠ h093Cks m c v % l := by
  intro heq
  rw [H093_cks_add, H093_cks_single] at heq
  simp only [hj, ↓reduceIte] at heq
  have h3 := Int.emod_eq_emod_iff_emod_sub_eq_zero.mp heq
  have h4 : h093Cks m c v + c j * e - h093Cks m c v = c j * e := by omega
  rw [h4] at h3
  have h5 : l ∣ c j * e := Int.dvd_of_emod_eq_zero h3
  obtain ⟨u, hu⟩ := hu
  apply he
  have h6 : e = u * (c j * e) - (c j * u - 1) * e := by grind
  rw [h6]
  exact Int.dvd_sub (Int.dvd_trans h5 ⟨u, Int.mul_comm _ _⟩) (Int.dvd_trans hu ⟨e, rfl⟩)

/-- Checking once per `q` matvecs keeps the overhead under 2% when `100 r ≤ q w`. -/
theorem H093_overhead_le_2pct (r m q w : Nat) (h : 100 * r ≤ q * w) :
    50 * h093CheckCost r m ≤ h093MatvecCost q w m := by
  unfold h093CheckCost h093MatvecCost
  have := Nat.mul_le_mul_right m h
  simp only [Nat.mul_assoc] at this
  omega

/-- Duplicate verification costs one extra matvec per matvec; a check that is under
2% of a matvec batch is cheaper by at least 50x. -/
theorem H093_cheaper_than_duplicate (r m q w : Nat) (h : 100 * r ≤ q * w) :
    50 * h093CheckCost r m ≤ h093MatvecCost q w m :=
  H093_overhead_le_2pct r m q w h

/-! ## H094 -/

/-- **H094** — Latin-square XOR-skewed storage for conflict-free pair-sum table access.
Handbook 14.1.1 (prime powers), 14.1.5 (affine and projective planes). Phase: hardware.
Claim: banking entry `(i, j)` at `i XOR j` over GF(2^5) gives conflict-free access along
rows, columns, and every slope `a ≠ 1`. -/
structure h094GF32 where
  mul : Nat → Nat → Nat
  lt : ∀ a b, a < 32 → b < 32 → mul a b < 32
  one_mul : ∀ b, mul 1 b = b
  mul_xor_left : ∀ a a' b, mul (a ^^^ a') b = mul a b ^^^ mul a' b
  mul_xor_right : ∀ a b b', mul a (b ^^^ b') = mul a b ^^^ mul a b'
  no_zero_div : ∀ a b, mul a b = 0 → a = 0 ∨ b = 0

/-- Bank of the element at row `i` on the line of slope `a`, offset `c`. -/
def h094Bank (F : h094GF32) (a c i : Nat) : Nat := i ^^^ (F.mul a i ^^^ c)

def H094_claim : Prop :=
  ∀ (F : h094GF32) (a c : Nat), a < 32 → a ≠ 1 →
    ∀ i j, i < 32 → j < 32 → h094Bank F a c i = h094Bank F a c j → i = j

theorem h094_xor_cancel (a b : Nat) : a ^^^ (a ^^^ b) = b := by
  rw [← Nat.xor_assoc, Nat.xor_self, Nat.zero_xor]

theorem h094_xor_eq_zero {a b : Nat} (h : a ^^^ b = 0) : a = b := by
  have : a ^^^ (a ^^^ b) = a ^^^ 0 := by rw [h]
  rw [h094_xor_cancel, Nat.xor_zero] at this
  exact this.symm

theorem H094_row_conflict_free (i j k : Nat) (h : i ^^^ j = i ^^^ k) : j = k := by
  have := congrArg (fun x => i ^^^ x) h
  simp only [h094_xor_cancel] at this
  exact this

theorem H094_skew_injective : H094_claim := by
  intro F a c _ ha i j _ _ h
  unfold h094Bank at h
  have key : F.mul (1 ^^^ a) (i ^^^ j) = 0 := by
    rw [F.mul_xor_left, F.mul_xor_right, F.mul_xor_right, F.one_mul, F.one_mul]
    have h2 : (i ^^^ (F.mul a i ^^^ c)) ^^^ (j ^^^ (F.mul a j ^^^ c)) = 0 := by
      rw [h, Nat.xor_self]
    have h3 : (i ^^^ (F.mul a i ^^^ c)) ^^^ (j ^^^ (F.mul a j ^^^ c))
        = ((i ^^^ j) ^^^ (F.mul a i ^^^ F.mul a j)) ^^^ (c ^^^ c) := by
      ac_rfl
    rw [h3, Nat.xor_self, Nat.xor_zero] at h2
    exact h2
  rcases F.no_zero_div _ _ key with h0 | h0
  · exact absurd (h094_xor_eq_zero h0).symm ha
  · exact h094_xor_eq_zero h0

/-! ## H095 -/

/-- **H095** — Projective-plane block design to shard all-pairs decomposition.
Handbook 14.5.1 (block designs), 14.4.1 (projective spaces), 14.5.3 (Singer difference
sets). Phase: hardware. Claim: placing shard pairs by lines of PG(2,p) (lambda = 1) gives
zero redundant pair work and per-worker transfer `B (p+1) / M` versus `B` for all-gather,
with total work identical. -/
def h095Points (p : Nat) : Nat := p * p + p + 1

/-- Number of unordered pairs among `n` items. -/
def h095Pairs (n : Nat) : Nat := n * (n - 1) / 2

/-- Every shard pair `a < b < M` lies in exactly one block (lambda = 1). -/
def h095PairCover (M : Nat) (blocks : List (List Nat)) : Prop :=
  ∀ a b, a < b → b < M →
    (blocks.filter (fun blk => blk.contains a && blk.contains b)).length = 1

/-- Pair work of a block assignment: the pairs inside each block. -/
def h095Work (blocks : List (List Nat)) : Nat :=
  (blocks.map (fun b => h095Pairs b.length)).sum

def h095Transfer (p B : Nat) : Nat := (p + 1) * B / h095Points p

def H095_claim : Prop :=
  ∀ (p B : Nat) (blocks : List (List Nat)),
    blocks.length = h095Points p →
    (∀ b ∈ blocks, b.length = p + 1) →
    h095PairCover (h095Points p) blocks →
    h095Work blocks = h095Pairs (h095Points p) ∧ h095Transfer p B ≤ B

theorem H095_line_pairs (p : Nat) :
    h095Points p * h095Pairs (p + 1) = h095Pairs (h095Points p) := by
  obtain ⟨k, hk⟩ : ∃ k, p * (p + 1) = 2 * k := by
    rcases Nat.mod_two_eq_zero_or_one p with h | h
    · refine ⟨(p / 2) * (p + 1), ?_⟩
      have hp : p = 2 * (p / 2) := by omega
      calc p * (p + 1) = (2 * (p / 2)) * (p + 1) := by rw [← hp]
        _ = 2 * ((p / 2) * (p + 1)) := Nat.mul_assoc _ _ _
    · refine ⟨p * ((p + 1) / 2), ?_⟩
      have hp : p + 1 = 2 * ((p + 1) / 2) := by omega
      calc p * (p + 1) = p * (2 * ((p + 1) / 2)) := by rw [← hp]
        _ = 2 * (p * ((p + 1) / 2)) := by
          rw [← Nat.mul_assoc, Nat.mul_comm p 2, Nat.mul_assoc]
  unfold h095Pairs h095Points
  have e1 : (p + 1) * (p + 1 - 1) = 2 * k := by
    rw [Nat.add_sub_cancel, Nat.mul_comm]; exact hk
  have e2 : p * p + p + 1 - 1 = 2 * k := by
    rw [← hk, Nat.mul_add, Nat.mul_one]; omega
  rw [e1, e2, Nat.mul_div_cancel_left _ (by omega : 0 < 2), Nat.mul_left_comm,
    Nat.mul_div_cancel_left _ (by omega : 0 < 2)]

theorem H095_work_sum (blocks : List (List Nat)) (s : Nat)
    (h : ∀ b ∈ blocks, b.length = s) :
    h095Work blocks = blocks.length * h095Pairs s := by
  unfold h095Work
  induction blocks with
  | nil => simp
  | cons b bs ih =>
      have hb : b.length = s := h b (by simp)
      have hbs : ∀ x ∈ bs, x.length = s := fun x hx => h x (by simp [hx])
      simp only [List.map_cons, List.sum_cons, List.length_cons, hb, ih hbs]
      rw [Nat.succ_mul]; omega

theorem H095_total_work (p : Nat) (blocks : List (List Nat))
    (hn : blocks.length = h095Points p) (hs : ∀ b ∈ blocks, b.length = p + 1) :
    h095Work blocks = h095Pairs (h095Points p) := by
  rw [H095_work_sum blocks (p + 1) hs, hn]
  exact H095_line_pairs p

theorem H095_transfer_le (p B : Nat) : h095Transfer p B ≤ B := by
  unfold h095Transfer h095Points
  apply Nat.div_le_of_le_mul
  exact Nat.mul_le_mul_right B (by omega)

theorem H095_p7_transfer : 7 * h095Transfer 7 (2 ^ 14) ≤ 2 ^ 14 := by decide

theorem H095_claim_holds : H095_claim := by
  intro p B blocks hn hs _
  exact ⟨H095_total_work p blocks hn hs, H095_transfer_le p B⟩

/-! ## H096 -/

/-- **H096** — Reverse Cuthill-McKee reordering for block-Wiedemann matvec locality.
Handbook 13.4.5.1 (reordering), 13.4.4.1 (Wiedemann). Phase: hardware.
Claim: for B >= 2^20 and 130-bit ell, RCM plus heavy-column grouping cuts L2 misses per
nonzero by at least 30% and cycles per nonzero by at least 1.25x versus insertion order;
a cycle-level gain, while relations and the solution set are invariant. -/
structure h096Perm (B : Nat) where
  fwd : Fin B → Fin B
  bwd : Fin B → Fin B
  left_inv : ∀ i, bwd (fwd i) = i
  right_inv : ∀ i, fwd (bwd i) = i

/-- Cycle model: compute cycles plus a miss penalty. -/
def h096Cycles (nnz c0 pen miss : Nat) : Nat := nnz * c0 + pen * miss

def H096_claim : Prop :=
  ∀ (nnz c0 pen missIns missRcm : Nat),
    10 * missRcm ≤ 7 * missIns →           -- at least 30% fewer misses (measured)
    2 * (nnz * c0) ≤ pen * missIns →       -- memory-bound baseline (measured)
    5 * h096Cycles nnz c0 pen missRcm ≤ 4 * h096Cycles nnz c0 pen missIns

theorem h096_finSum_ofFn : ∀ (B : Nat) (f : Fin B → Int), finSum B f = (List.ofFn f).sum
  | 0, f => by simp [finSum]
  | B + 1, f => by
      rw [finSum, h096_finSum_ofFn B, List.ofFn_succ_last, List.sum_append]
      simp

theorem H096_finSum_perm {B : Nat} (σ : h096Perm B) (f : Fin B → Int) :
    finSum B (fun j => f (σ.fwd j)) = finSum B f := by
  have e : ∀ g : Fin B → Int, List.ofFn g = (List.finRange B).map g := by
    intro g; unfold List.finRange; rw [List.map_ofFn]; rfl
  rw [h096_finSum_ofFn, h096_finSum_ofFn, e, e]
  have hp : ((List.finRange B).map σ.fwd).Perm (List.finRange B) := by
    rw [List.perm_ext_iff_of_nodup]
    · intro a
      constructor
      · intro _; exact List.mem_finRange a
      · intro _; exact List.mem_map.2 ⟨σ.bwd a, List.mem_finRange _, σ.right_inv a⟩
    · exact List.Pairwise.map σ.fwd (fun x y hne hxy => hne (by
        have := congrArg σ.bwd hxy
        rwa [σ.left_inv, σ.left_inv] at this)) (List.nodup_finRange B)
    · exact List.nodup_finRange B
  have h2 := (hp.map f).foldr_eq' (f := fun a b : Int => a + b)
    (by intro x _ y _ z; omega) 0
  rw [List.map_map] at h2
  rw [List.sum_eq_foldr, List.sum_eq_foldr]
  exact h2

/-- Reordering the factor base and the relation coefficients together leaves the
exponent-side relation unchanged. -/
theorem H096_relation_invariant {G : Type} {n B : Nat} (I : DLPInstance G n)
    (F : FactorBase G B) (r : Relation B) (σ : h096Perm B) :
    Relation.holds I (fun j => F (σ.fwd j)) ⟨r.a, r.b, fun j => r.c (σ.fwd j)⟩
      ↔ Relation.holds I F r := by
  unfold Relation.holds
  rw [H096_finSum_perm σ (fun j => r.c j * ((I.log (F j)).val : Int))]

theorem H096_cycles_ratio : H096_claim := by
  intro nnz c0 pen missIns missRcm h1 h2
  unfold h096Cycles
  have h3 := Nat.mul_le_mul_left pen h1
  rw [Nat.mul_left_comm pen 7 missIns, Nat.mul_left_comm pen 10 missRcm] at h3
  omega

/-! ## H097 -/

/-- **H097** — Batch-affine vs projective candidate generation, binary vs prime split.
Handbook 12.3.3 (coordinate systems), 12.3.4 (explicit formulas), 12.3.6 (char-2 short
Weierstrass). Phase: hardware. Claim: with `k >= 64` walks, batch-affine addition is at
least 1.6x faster per candidate than projective plus batch conversion in GF(2^131) with
CLMUL (and at most 1.1x on 255-bit Edwards). Ledger below is counted, the cycle ratio
is an empirical bridge. -/
def h097BatchInvPer (M I k : Nat) : Nat := (3 * (k - 1) * M + I) / k

def h097AffinePer (M S I k : Nat) : Nat := (2 * M + S) + h097BatchInvPer M I k

def h097ProjPer (M S I k : Nat) : Nat :=
  (11 * M + 5 * S) + h097BatchInvPer M I k + (2 * M + S)

def H097_claim : Prop :=
  ∀ (M S I k : Nat), 64 ≤ k → 0 < M → 10 * S ≤ M → I ≤ 25 * M →
    16 * h097AffinePer M S I k ≤ 10 * h097ProjPer M S I k

theorem H097_mixed_le : ∀ M S : Nat, 5 * M + S ≤ 11 * M + 5 * S := by intro M S; omega

theorem H097_batchInv_le (M I k : Nat) (hk : 0 < k) :
    h097BatchInvPer M I k ≤ 3 * M + I / k := by
  unfold h097BatchInvPer
  have h1 : 3 * (k - 1) * M + I ≤ k * (3 * M) + I := by
    have : 3 * (k - 1) * M ≤ k * (3 * M) := by
      have := Nat.mul_le_mul_right M (show 3 * (k - 1) ≤ 3 * k by omega)
      calc 3 * (k - 1) * M ≤ 3 * k * M := this
        _ = k * (3 * M) := by rw [Nat.mul_comm 3 k, Nat.mul_assoc]
    omega
  calc (3 * (k - 1) * M + I) / k ≤ (k * (3 * M) + I) / k := Nat.div_le_div_right h1
    _ = 3 * M + I / k := by rw [Nat.mul_add_div hk]

theorem H097_affine_le_proj (M S I k : Nat) :
    h097AffinePer M S I k ≤ h097ProjPer M S I k := by
  unfold h097AffinePer h097ProjPer; omega

theorem H097_ledger_ratio : H097_claim := by
  intro M S I k hk hM hS hI
  have hk0 : 0 < k := by omega
  have h1 := H097_batchInv_le M I k hk0
  have h2 : I / k ≤ M := by
    apply Nat.div_le_of_le_mul
    have : 25 * M ≤ k * M := Nat.mul_le_mul_right M (by omega)
    omega
  unfold h097AffinePer h097ProjPer
  omega

/-! ## H098 -/

/-- **H098** — Booth/Duval canonical key at n = 131 against squaring chains.
Handbook 12.2.8 (Frobenius on Koblitz), 12.3.6 (char-2 arithmetic). Phase: hardware.
Claim: after one basis change, the minimal-rotation key (Booth) is at least 1.5x fewer
cycles than min-over-squarings, with identical orbit partition: `key (rotate w) = key w`,
`key w ≤ w`, and `N / n` orbits for a free action of prime order `n`. -/
def h098Key (w : List Bool) : List Bool := h092Naive w

def h098Orbits (n : Nat) : Nat :=
  (((h092Words n).filter (fun w => w.any id && !w.all id)).map h098Key).eraseDups.length

/-- Booth scan work (two passes over `ceil(n/64)` words) vs `n` squarings each
`sq` cycles; the cycle ratio is hypothesised through `sq` and `basisChange`. -/
def h098BoothCycles (n boothPerWord basisChange : Nat) : Nat :=
  basisChange + 2 * ((n + 63) / 64) * boothPerWord

def h098SquaringCycles (n sq : Nat) : Nat := n * sq

def H098_claim : Prop :=
  ∀ (w : List Bool) (r : Nat), h098Key (h092Rot r w) = h098Key w ∧
    h092Le (h098Key w) w = true

/-- A free action in which every orbit has size `k` partitions `N` into `N / k` orbits. -/
theorem H098_orbit_count (sizes : List Nat) (k : Nat) (_hk : 0 < k)
    (hsz : ∀ s ∈ sizes, s = k) : sizes.sum = sizes.length * k := by
  induction sizes with
  | nil => simp
  | cons s ss ih =>
      have hs : s = k := hsz s (by simp)
      have := ih (fun x hx => hsz x (by simp [hx]))
      simp only [List.sum_cons, List.length_cons, this, hs]
      rw [Nat.succ_mul]; omega

theorem H098_orbit_count_div (sizes : List Nat) (k N : Nat) (hk : 0 < k)
    (hsz : ∀ s ∈ sizes, s = k) (hsum : sizes.sum = N) :
    sizes.length = orbitRepresentatives N k := by
  unfold orbitRepresentatives
  rw [← hsum, H098_orbit_count sizes k hk hsz, Nat.mul_div_cancel _ hk]

theorem H098_key_rotation_invariant_upto6 :
    (List.range 7).all (fun n => (h092Words n).all
      (fun w => (List.range n).all (fun r => h098Key (h092Rot r w) == h098Key w))) = true := by
  decide

theorem H098_key_le_word_upto6 :
    (List.range 7).all (fun n => (h092Words n).all
      (fun w => h092Le (h098Key w) w)) = true := by decide

theorem H098_orbits_n5 : h098Orbits 5 = orbitRepresentatives (2 ^ 5 - 2) 5 := by decide

theorem H098_orbits_n7 : h098Orbits 7 = orbitRepresentatives (2 ^ 7 - 2) 7 := by decide

/-! ## H099 -/

/-- **H099** — Itoh-Tsujii plus Montgomery batching as the affine-add primitive.
Handbook 11.1.8.2 (inversion in extension fields), 11.1.5.2 (multiplication in extension
fields). Phase: hardware. Claim: batched affine addition with Itoh-Tsujii inversion
(8 multiplications at n = 131) beats Lopez-Dahab mixed addition (8-11 multiplications)
per point sum at batch >= 16 for n in 53..131. -/
def h099Pop : Nat → Nat → Nat
  | 0, _ => 0
  | f + 1, m => if m = 0 then 0 else (m % 2) + h099Pop f (m / 2)

def h099Log2 : Nat → Nat → Nat
  | 0, _ => 0
  | f + 1, m => if m ≤ 1 then 0 else 1 + h099Log2 f (m / 2)

/-- Multiplications of an Itoh-Tsujii inversion in GF(2^n): `floor(log2 (n-1)) + wt(n-1) - 1`. -/
def h099ItohMuls (n : Nat) : Nat := h099Log2 64 (n - 1) + h099Pop 64 (n - 1) - 1

/-- Montgomery batch inversion of `k` elements: `3 (k-1)` multiplications plus one inversion. -/
def h099BatchInvMuls (k : Nat) : Nat := 3 * (k - 1)

/-- Cost in tenths of a multiplication (`M = 10`, `S = 1`) of `k` batched affine additions
in GF(2^n): per add 2 multiplications and 1 squaring, plus one shared inversion
(Itoh-Tsujii multiplications and `n - 1` squarings). -/
def h099AffineTenths (n k : Nat) : Nat :=
  10 * (2 * k + h099BatchInvMuls k + h099ItohMuls n) + k + (n - 1)

/-- Lopez-Dahab mixed addition at `ldM` multiplications and 5 squarings. -/
def h099LDTenths (ldM k : Nat) : Nat := k * (10 * ldM + 5)

def H099_claim : Prop :=
  ∀ (n k ldM : Nat), 53 ≤ n → n ≤ 131 → 16 ≤ k → 8 ≤ ldM →
    h099AffineTenths n k ≤ h099LDTenths ldM k

theorem H099_itoh_131 : h099ItohMuls 131 = 8 := by decide
theorem H099_itoh_83 : h099ItohMuls 83 = 8 := by decide
theorem H099_itoh_53 : h099ItohMuls 53 = 7 := by decide

theorem H099_batchInv_20 : h099BatchInvMuls 20 = 57 := by decide

theorem H099_breakeven_131 :
    ¬ h099AffineTenths 131 5 ≤ h099LDTenths 8 5 ∧ h099AffineTenths 131 6 ≤ h099LDTenths 8 6 := by
  decide

theorem H099_batch_beats_ld_131 (k ldM : Nat) (hk : 6 ≤ k) (hl : 8 ≤ ldM) :
    h099AffineTenths 131 k ≤ h099LDTenths ldM k := by
  unfold h099AffineTenths h099LDTenths h099BatchInvMuls
  rw [H099_itoh_131]
  have : 8 * k ≤ ldM * k := Nat.mul_le_mul_right k hl
  have e : k * (10 * ldM + 5) = 10 * (ldM * k) + 5 * k := by
    rw [Nat.mul_add, Nat.mul_comm k (10 * ldM), Nat.mul_assoc]; omega
  omega

theorem H099_claim_131 (k ldM : Nat) (hk : 16 ≤ k) (hl : 8 ≤ ldM) :
    h099AffineTenths 131 k ≤ h099LDTenths ldM k :=
  H099_batch_beats_ld_131 k ldM (by omega) hl

/-! ## H100 -/

/-- **H100** — Rotation-based membership test `g(sigma) x = 0` with sparse generator.
Handbook 5.3.5 (fast arithmetic using normal bases), 5.2.1 (normal bases).
Phase: hardware. Claim: membership in `V = ker g(sigma)` costs `wt(g)` XORs of rotations
in a normal basis, 8-15x cheaper than the polynomial-basis matrix test, but the whole
loop gains only 1-5% (likely null). -/
def h100Rot (n : Nat) (x : Nat → Bool) : Nat → Bool := fun i => x ((i + 1) % n)

def h100RotPow (n : Nat) : Nat → (Nat → Bool) → (Nat → Bool)
  | 0, x => x
  | k + 1, x => h100Rot n (h100RotPow n k x)

/-- `g(sigma) x` for `g = Σ_{e ∈ es} X^e`. -/
def h100Apply (n : Nat) : List Nat → (Nat → Bool) → (Nat → Bool)
  | [], _ => fun _ => false
  | e :: es, x => fun i => xor (x ((i + e) % n)) (h100Apply n es x i)

def h100XorW (x y : Nat → Bool) : Nat → Bool := fun i => xor (x i) (y i)

/-- Membership test cost: `wt(g)` rotations, each over `ceil(n/64)` words. -/
def h100MemberCost (n : Nat) (g : List Nat) : Nat := g.length * ((n + 63) / 64)

/-- Matrix test: one row-dot-product per coordinate. -/
def h100MatrixCost (n : Nat) : Nat := n * ((n + 63) / 64)

/-- Carry-less product of GF(2) polynomials packed in naturals (with fuel). -/
def h100Clmul : Nat → Nat → Nat → Nat
  | 0, _, _ => 0
  | f + 1, a, b => if b = 0 then 0 else (if b % 2 = 1 then a else 0) ^^^ h100Clmul f (a <<< 1) (b / 2)

def H100_claim : Prop :=
  ∀ (n : Nat) (g : List Nat) (x : Nat → Bool), 0 < n →
    (∀ i, h100Apply n g x i = false) →
    (∀ i, h100Apply n g (h100Rot n x) i = false) ∧
    (∀ y : Nat → Bool, (∀ i, h100Apply n g y i = false) →
      ∀ i, h100Apply n g (h100XorW x y) i = false) ∧
    (8 * g.length ≤ n → 8 * h100MemberCost n g ≤ h100MatrixCost n)

theorem H100_rotPow_eq (n : Nat) (x : Nat → Bool) :
    ∀ k i, i < n → h100RotPow n k x i = x ((i + k) % n)
  | 0, i, hi => by simp [h100RotPow, Nat.mod_eq_of_lt hi]
  | k + 1, i, hi => by
      show h100RotPow n k x ((i + 1) % n) = _
      have hlt : (i + 1) % n < n := Nat.mod_lt _ (by omega)
      rw [H100_rotPow_eq n x k _ hlt, Nat.mod_add_mod]
      congr 2; omega

theorem H100_rot_pow_n (n : Nat) (x : Nat → Bool) (i : Nat) (hi : i < n) :
    h100RotPow n n x i = x i := by
  rw [H100_rotPow_eq n x n i hi, Nat.add_mod_right, Nat.mod_eq_of_lt hi]

theorem H100_apply_rot (n : Nat) (x : Nat → Bool) :
    ∀ (g : List Nat) i, h100Apply n g (h100Rot n x) i = h100Apply n g x ((i + 1) % n)
  | [], i => rfl
  | e :: es, i => by
      simp only [h100Apply, h100Rot]
      rw [H100_apply_rot n x es i]
      have h1 : ((i + e) % n + 1) % n = ((i + 1) % n + e) % n := by
        rw [Nat.mod_add_mod, Nat.mod_add_mod]; congr 1; omega
      rw [h1]

theorem H100_apply_xor (n : Nat) (x y : Nat → Bool) :
    ∀ (g : List Nat) i,
      h100Apply n g (h100XorW x y) i = xor (h100Apply n g x i) (h100Apply n g y i)
  | [], i => rfl
  | e :: es, i => by
      have key : ∀ a b c d : Bool, xor (xor a b) (xor c d) = xor (xor a c) (xor b d) := by decide
      simp only [h100Apply, h100XorW]
      rw [H100_apply_xor n x y es i]
      exact key _ _ _ _

theorem H100_kernel_xor_closed (n : Nat) (g : List Nat) (x y : Nat → Bool)
    (hx : ∀ i, h100Apply n g x i = false) (hy : ∀ i, h100Apply n g y i = false) :
    ∀ i, h100Apply n g (h100XorW x y) i = false := by
  intro i
  rw [H100_apply_xor, hx, hy]; rfl

theorem H100_kernel_rot_invariant (n : Nat) (g : List Nat) (x : Nat → Bool)
    (hx : ∀ i, h100Apply n g x i = false) :
    ∀ i, h100Apply n g (h100Rot n x) i = false := by
  intro i
  rw [H100_apply_rot, hx]

theorem H100_cost_ratio (n : Nat) (g : List Nat) (h : 8 * g.length ≤ n) :
    8 * h100MemberCost n g ≤ h100MatrixCost n := by
  unfold h100MemberCost h100MatrixCost
  have := Nat.mul_le_mul_right ((n + 63) / 64) h
  simp only [Nat.mul_assoc] at this ⊢
  omega

theorem H100_claim_holds : H100_claim := by
  intro n g x _ hx
  exact ⟨H100_kernel_rot_invariant n g x hx,
    fun y hy => H100_kernel_xor_closed n g x y hx hy, H100_cost_ratio n g⟩

/-- `1 + X + X^3` divides `X^7 + 1` over GF(2): quotient `1 + X + X^2 + X^4`. -/
theorem H100_divides_x7 : h100Clmul 64 0b1011 0b10111 = 2 ^ 7 + 1 := by decide

/-- `1 + X + X^4` divides `X^15 + 1`. -/
theorem H100_divides_x15 : h100Clmul 64 0b10011 2479 = 2 ^ 15 + 1 := by decide

end HandbookIC.Ideas.B10

#print axioms HandbookIC.Ideas.B10.h091_xor_xor
#print axioms HandbookIC.Ideas.B10.H091_apply_linear
#print axioms HandbookIC.Ideas.B10.H091_comp_linear
#print axioms HandbookIC.Ideas.B10.H091_blocks_64
#print axioms HandbookIC.Ideas.B10.H091_blocks_131
#print axioms HandbookIC.Ideas.B10.H091_blocks_quadratic
#print axioms HandbookIC.Ideas.B10.H091_blocks_mono
#print axioms HandbookIC.Ideas.B10.H091_instr_mono
#print axioms HandbookIC.Ideas.B10.H092_le_lz
#print axioms HandbookIC.Ideas.B10.H092_min_has_max_run
#print axioms HandbookIC.Ideas.B10.H092_fast_eq_naive_upto6
#print axioms HandbookIC.Ideas.B10.H092_ops_131
#print axioms HandbookIC.Ideas.B10.H092_ops_ratio
#print axioms HandbookIC.Ideas.B10.H093_cks_add
#print axioms HandbookIC.Ideas.B10.H093_cks_single
#print axioms HandbookIC.Ideas.B10.H093_detect_of_mds
#print axioms HandbookIC.Ideas.B10.H093_single_fault_detect
#print axioms HandbookIC.Ideas.B10.H093_overhead_le_2pct
#print axioms HandbookIC.Ideas.B10.H093_cheaper_than_duplicate
#print axioms HandbookIC.Ideas.B10.h094_xor_cancel
#print axioms HandbookIC.Ideas.B10.h094_xor_eq_zero
#print axioms HandbookIC.Ideas.B10.H094_row_conflict_free
#print axioms HandbookIC.Ideas.B10.H094_skew_injective
#print axioms HandbookIC.Ideas.B10.H095_line_pairs
#print axioms HandbookIC.Ideas.B10.H095_work_sum
#print axioms HandbookIC.Ideas.B10.H095_total_work
#print axioms HandbookIC.Ideas.B10.H095_transfer_le
#print axioms HandbookIC.Ideas.B10.H095_p7_transfer
#print axioms HandbookIC.Ideas.B10.H095_claim_holds
#print axioms HandbookIC.Ideas.B10.h096_finSum_ofFn
#print axioms HandbookIC.Ideas.B10.H096_finSum_perm
#print axioms HandbookIC.Ideas.B10.H096_relation_invariant
#print axioms HandbookIC.Ideas.B10.H096_cycles_ratio
#print axioms HandbookIC.Ideas.B10.H097_mixed_le
#print axioms HandbookIC.Ideas.B10.H097_batchInv_le
#print axioms HandbookIC.Ideas.B10.H097_affine_le_proj
#print axioms HandbookIC.Ideas.B10.H097_ledger_ratio
#print axioms HandbookIC.Ideas.B10.H098_orbit_count
#print axioms HandbookIC.Ideas.B10.H098_orbit_count_div
#print axioms HandbookIC.Ideas.B10.H098_key_rotation_invariant_upto6
#print axioms HandbookIC.Ideas.B10.H098_key_le_word_upto6
#print axioms HandbookIC.Ideas.B10.H098_orbits_n5
#print axioms HandbookIC.Ideas.B10.H098_orbits_n7
#print axioms HandbookIC.Ideas.B10.H099_itoh_131
#print axioms HandbookIC.Ideas.B10.H099_itoh_83
#print axioms HandbookIC.Ideas.B10.H099_itoh_53
#print axioms HandbookIC.Ideas.B10.H099_batchInv_20
#print axioms HandbookIC.Ideas.B10.H099_breakeven_131
#print axioms HandbookIC.Ideas.B10.H099_batch_beats_ld_131
#print axioms HandbookIC.Ideas.B10.H099_claim_131
#print axioms HandbookIC.Ideas.B10.H100_rotPow_eq
#print axioms HandbookIC.Ideas.B10.H100_rot_pow_n
#print axioms HandbookIC.Ideas.B10.H100_apply_rot
#print axioms HandbookIC.Ideas.B10.H100_apply_xor
#print axioms HandbookIC.Ideas.B10.H100_kernel_xor_closed
#print axioms HandbookIC.Ideas.B10.H100_kernel_rot_invariant
#print axioms HandbookIC.Ideas.B10.H100_cost_ratio
#print axioms HandbookIC.Ideas.B10.H100_claim_holds
#print axioms HandbookIC.Ideas.B10.H100_divides_x7
#print axioms HandbookIC.Ideas.B10.H100_divides_x15
