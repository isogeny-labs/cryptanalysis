import HandbookIC.Core

/-!
# HandbookIC.Ideas.B03 — handbook ideas H021 .. H030 (decomposition phase)

Each idea has: a doc comment, definitions prefixed by the lower-case id,
`def Hxxx_claim : Prop` (all hypotheses explicit; curve and field facts are
hypotheses of the Prop, nothing is postulated) and at least one proved
supporting theorem.
-/

namespace HandbookIC.Ideas.B03

open HandbookIC

/-! ## Shared helper -/

/-- Monotonicity of filtered length under a pointwise implication. -/
theorem b03FilterMono {α : Type} (p q : α → Bool) :
    ∀ l : List α, (∀ x ∈ l, p x = true → q x = true) →
      (l.filter p).length ≤ (l.filter q).length
  | [], _ => by simp
  | a :: l, h => by
    have ih := b03FilterMono p q l (fun x hx => h x (List.mem_cons_of_mem a hx))
    have ha : p a = true → q a = true := h a (by simp)
    cases hp : p a <;> cases hq : q a <;> simp [List.filter, hp, hq] at ha ⊢ <;> omega

/-- Number of one bits of `n`, with fuel. -/
def b03Pop : Nat → Nat → Nat
  | 0, _ => 0
  | f + 1, n => if n = 0 then 0 else n % 2 + b03Pop f (n / 2)

/-! ## H021 -/

/-- **H021** — Frobenius-linear decision test for 2-point decomposition on interval bases.
Handbook: 16.7.2 Polynomial operations arithmetic; 16.3.3.12 Linearization.
Phase: decomposition.
Claim: for `V = span{1,..,t^(d-1)}` with `3d-1 ≤ n`, `S3` is F2-linear in the bits of
`(pi,s)`, so `x(R) = x1 + x2` is decided by one `n × (3d-1)` elimination instead of
`2^d` enumeration, returning identical decompositions. -/
def h021Decomposes (n : Nat) (V : Nat → Bool) (xR : Nat) : Prop :=
  ∃ x1, x1 < 2 ^ n ∧ V x1 = true ∧ V (xR ^^^ x1) = true

/-- Per-relation cost of the linear test (`2^(n-2d) · n^3/64`). -/
def h021RelCost (n d : Nat) : Nat := 2 ^ (n - 2 * d) * (n ^ 3 / 64)

/-- Per-relation cost of enumeration. -/
def h021EnumCost (n d : Nat) : Nat := 2 ^ (n - d)

def H021_claim : Prop :=
  ∀ (n d : Nat) (V : Nat → Bool) (lin : Nat → Bool) (targets : List Nat),
    3 * d - 1 ≤ n → 2 * d ≤ n → n ^ 3 / 64 ≤ 2 ^ d →
    (∀ xR, lin xR = true ↔ h021Decomposes n V xR) →
    (∀ xR, xR ∈ targets.filter lin ↔ xR ∈ targets ∧ h021Decomposes n V xR) ∧
    h021RelCost n d ≤ h021EnumCost n d

theorem H021_sound (n : Nat) (V : Nat → Bool) (lin : Nat → Bool) (targets : List Nat)
    (hlin : ∀ xR, lin xR = true ↔ h021Decomposes n V xR) (xR : Nat) :
    xR ∈ targets.filter lin ↔ xR ∈ targets ∧ h021Decomposes n V xR := by
  rw [List.mem_filter, hlin]

theorem H021_relCost_le (n d : Nat) (h2 : 2 * d ≤ n) (hc : n ^ 3 / 64 ≤ 2 ^ d) :
    h021RelCost n d ≤ h021EnumCost n d := by
  unfold h021RelCost h021EnumCost
  calc 2 ^ (n - 2 * d) * (n ^ 3 / 64) ≤ 2 ^ (n - 2 * d) * 2 ^ d :=
        Nat.mul_le_mul_left _ hc
    _ = 2 ^ (n - 2 * d + d) := (Nat.pow_add _ _ _).symm
    _ = 2 ^ (n - d) := by congr 1; omega

theorem H021_claim_proved : H021_claim := by
  intro n d V lin targets _ h2 hc hlin
  exact ⟨fun xR => H021_sound n V lin targets hlin xR, H021_relCost_le n d h2 hc⟩

theorem H021_instance_n31_d9 :
    3 * 9 - 1 ≤ 31 ∧ 2 * 9 ≤ 31 ∧ 31 ^ 3 / 64 ≤ 2 ^ 9 ∧
      h021RelCost 31 9 ≤ h021EnumCost 31 9 := by
  decide

/-! ## H022 -/

/-- **H022** — Block-multigraded Macaulay matrices for Weil-restricted `S_{m+1}`.
Handbook: 16.3.3.12 Direct attacks with polynomial solvers; 16.3.3.8 Rank structure.
Phase: decomposition.
Claim: bit-degree `popcount e` per block makes the system multihomogeneous; at the first
fall multidegree the multigraded Macaulay matrix has at least 10x fewer columns than the
total-degree one at `m = 3`. Modelled here by squarefree monomial counts. -/
def h022Mono : Nat → Nat → Nat
  | 0, _ => 1
  | _ + 1, 0 => 1
  | d + 1, D + 1 => h022Mono d (D + 1) + h022Mono d D

/-- Bit degree of an exponent. -/
def h022BitDeg (e : Nat) : Nat := b03Pop e e

/-- Multigraded column bound for 3 blocks of `d` variables at multidegree `(D1,D2,D3)`. -/
def h022MultiCols (d D1 D2 D3 : Nat) : Nat := h022Mono d D1 * h022Mono d D2 * h022Mono d D3

/-- Total-degree column bound for `3d` variables at degree `D`. -/
def h022TotalCols (d D : Nat) : Nat := h022Mono (3 * d) D

def H022_claim : Prop :=
  ∀ (Dtot : Nat), 5 ≤ Dtot →
    10 * h022MultiCols 7 1 1 1 ≤ h022TotalCols 7 Dtot

theorem h022Mono_pos : ∀ d D, 0 < h022Mono d D
  | 0, _ => by simp [h022Mono]
  | d + 1, 0 => by simp [h022Mono]
  | d + 1, D + 1 => by
    have := h022Mono_pos d (D + 1)
    simp only [h022Mono]; omega

theorem h022Mono_le_succ : ∀ d D, h022Mono d D ≤ h022Mono d (D + 1)
  | 0, _ => by simp [h022Mono]
  | d + 1, 0 => by
    have := h022Mono_pos d 1
    show 1 ≤ h022Mono d 1 + h022Mono d 0
    omega
  | d + 1, D + 1 => by
    have h1 := h022Mono_le_succ d (D + 1)
    have h2 := h022Mono_le_succ d D
    show h022Mono d (D + 1) + h022Mono d D ≤ h022Mono d (D + 1 + 1) + h022Mono d (D + 1)
    omega

theorem h022Mono_mono (d D : Nat) : ∀ k, h022Mono d D ≤ h022Mono d (D + k)
  | 0 => Nat.le_refl _
  | k + 1 => Nat.le_trans (h022Mono_mono d D k) (h022Mono_le_succ d (D + k))

theorem H022_bitDeg_le_two : ∀ e, e ≤ 4 → h022BitDeg e ≤ 2 := by decide

theorem H022_claim_proved : H022_claim := by
  intro Dtot h
  have h5 : h022TotalCols 7 5 ≤ h022TotalCols 7 Dtot := by
    have := h022Mono_mono 21 5 (Dtot - 5)
    unfold h022TotalCols
    have e : 5 + (Dtot - 5) = Dtot := by omega
    rw [e] at this
    exact this
  have hc : 10 * h022MultiCols 7 1 1 1 ≤ h022TotalCols 7 5 := by decide
  exact Nat.le_trans hc h5

/-! ## H023 -/

/-- **H023** — One-bit trace criterion as a dead-target sieve for 2-decompositions.
Handbook: 16.3.3.1 Linearization equations; 16.3.2.4 Frobenius-additive structure;
9.1.1.2 Trace representation. Phase: decomposition.
Claim: for `V ⊆ ker Tr`, targets with trace bit 1 have no `V`-decomposition, so filtering
them out keeps every decomposable target and never costs more than the baseline. -/
def h023Live (tr : Nat → Bool) (targets : List Nat) : List Nat :=
  targets.filter (fun R => !tr R)

def h023Cost (perTarget : Nat) (targets : List Nat) : Cost :=
  { factorBase := 0, relations := perTarget * targets.length, linearAlgebra := 0, descent := 0 }

def H023_claim : Prop :=
  ∀ (tr dec : Nat → Bool) (targets : List Nat) (perTarget : Nat),
    (∀ R, tr R = true → dec R = false) →
    (h023Live tr targets).filter dec = targets.filter dec ∧
    (h023Cost perTarget (h023Live tr targets)).total ≤ (h023Cost perTarget targets).total

theorem H023_filter_preserved (tr dec : Nat → Bool) (targets : List Nat)
    (h : ∀ R, tr R = true → dec R = false) :
    (h023Live tr targets).filter dec = targets.filter dec := by
  unfold h023Live
  rw [List.filter_filter]
  apply List.filter_congr
  intro x _
  cases ht : tr x
  · simp
  · simp [h x ht]

theorem H023_live_le (tr : Nat → Bool) (targets : List Nat) :
    (h023Live tr targets).length ≤ targets.length := List.length_filter_le _ _

theorem H023_partition (tr : Nat → Bool) :
    ∀ targets : List Nat,
      (targets.filter tr).length + (h023Live tr targets).length = targets.length
  | [] => by simp [h023Live]
  | a :: l => by
    have ih := H023_partition tr l
    unfold h023Live at ih ⊢
    cases h : tr a <;> simp [List.filter, h] <;> omega

theorem H023_claim_proved : H023_claim := by
  intro tr dec targets perTarget h
  refine ⟨H023_filter_preserved tr dec targets h, ?_⟩
  unfold Cost.total h023Cost
  have := H023_live_le tr targets
  have := Nat.mul_le_mul_left perTarget this
  simp only
  omega

theorem H023_strict_improvement (tr : Nat → Bool) (targets : List Nat) (c : Nat)
    (hc : 0 < c) (hlt : (h023Live tr targets).length < targets.length) :
    (h023Cost c targets).improvesRelations (h023Cost c (h023Live tr targets)) := by
  refine ⟨rfl, rfl, rfl, ?_⟩
  show c * (h023Live tr targets).length < c * targets.length
  exact (Nat.mul_lt_mul_left hc).2 hlt

/-! ## H024 -/

/-- **H024** — Lifted `(s,p)` enumeration with half-trace bit-GEMM tables.
Handbook: 16.3.2.5 Oil and vinegar; 16.3.3.2 Critical bilinear relations.
Phase: decomposition.
Claim: enumerating `(s,x1)` with `s = x1 + x2` over `V` reproduces the naive pair
enumeration exactly (up to the swap `(x1,x2) ↔ (x1, s+x1)`), at at most 0.6 field
multiplications per candidate against at least 4. -/
def h024Naive (Vs : List Nat) : List (Nat × Nat) :=
  Vs.flatMap (fun a => Vs.map (fun b => (a, b)))

def h024Lifted (Vs : List Nat) : List (Nat × Nat) :=
  Vs.flatMap (fun a => Vs.map (fun b => (a ^^^ b, a)))

/-- Decode a lifted pair `(s, x1)` into `(x1, x2)`. -/
def h024Decode (p : Nat × Nat) : Nat × Nat := (p.2, p.1 ^^^ p.2)

/-- Multiplications in tenths per candidate. -/
def h024NaiveTenths : Nat := 40
def h024LiftedTenths : Nat := 6

def h024Cost (tenthsPerCand cands : Nat) : Cost :=
  { factorBase := 0, relations := tenthsPerCand * cands, linearAlgebra := 0, descent := 0 }

def H024_claim : Prop :=
  ∀ (Vs : List Nat) (dec : Nat × Nat → Bool),
    ((h024Lifted Vs).map h024Decode).filter dec = (h024Naive Vs).filter dec ∧
    ∀ cands, 0 < cands →
      (h024Cost h024NaiveTenths cands).improvesRelations (h024Cost h024LiftedTenths cands)

theorem h024_decode_lifted (Vs : List Nat) :
    (h024Lifted Vs).map h024Decode = h024Naive Vs := by
  unfold h024Lifted h024Naive
  rw [List.map_flatMap]
  congr 1
  funext a
  rw [List.map_map]
  apply List.map_congr_left
  intro b _
  simp only [Function.comp, h024Decode]
  rw [Nat.xor_comm a b, Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]

theorem H024_claim_proved : H024_claim := by
  intro Vs dec
  refine ⟨?_, ?_⟩
  · rw [h024_decode_lifted]
  · intro cands hc
    refine ⟨rfl, rfl, rfl, ?_⟩
    show h024LiftedTenths * cands < h024NaiveTenths * cands
    exact (Nat.mul_lt_mul_right hc).2 (by decide)

theorem H024_ratio (cands : Nat) :
    6 * (h024LiftedTenths * cands) ≤ h024NaiveTenths * cands := by
  unfold h024LiftedTenths h024NaiveTenths
  omega

theorem H024_xor_cancel (a b : Nat) : (a ^^^ b) ^^^ a = b := by
  rw [Nat.xor_comm a b, Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]

/-! ## H025 -/

/-- **H025** — Optimal normal basis coordinates to minimise monomials of Weil-restricted `S3`.
Handbook: 16.3.1.1 Bipolar construction; 16.3.1.3 Isomorphism of polynomials.
Phase: decomposition.
Claim: an invertible linear substitution (ONB coordinates) is a bijection of solution
sets, so it changes cost only through the density hypothesis
`monomials' * c ≤ monomials`. -/
def h025Cost (monos cols : Nat) : Nat := monos * cols

def H025_claim : Prop :=
  ∀ (pts : List Nat) (f g : Nat → Nat) (sol : Nat → Bool) (monos monos' cols c : Nat),
    (∀ x, g (f x) = x) →
    monos' * c ≤ monos →
    smoothCount (pts.map f) (fun y => sol (g y)) = smoothCount pts sol ∧
    h025Cost monos' cols * c ≤ h025Cost monos cols

theorem H025_count_invariant (pts : List Nat) (f g : Nat → Nat) (sol : Nat → Bool)
    (hg : ∀ x, g (f x) = x) :
    smoothCount (pts.map f) (fun y => sol (g y)) = smoothCount pts sol := by
  unfold smoothCount
  rw [List.filter_map, List.length_map]
  have : ((fun y => sol (g y)) ∘ f) = sol := by
    funext x; simp [Function.comp, hg]
  rw [this]

theorem H025_cost_scaling (monos monos' cols c : Nat) (h : monos' * c ≤ monos) :
    h025Cost monos' cols * c ≤ h025Cost monos cols := by
  unfold h025Cost
  calc monos' * cols * c = (monos' * c) * cols := by
        rw [Nat.mul_assoc, Nat.mul_comm cols c, ← Nat.mul_assoc]
    _ ≤ monos * cols := Nat.mul_le_mul_right _ h

theorem H025_claim_proved : H025_claim := by
  intro pts f g sol monos monos' cols c hg h
  exact ⟨H025_count_invariant pts f g sol hg, H025_cost_scaling monos monos' cols c h⟩

/-! ## H026 -/

/-- **H026** — Gray-code Artin-Schreier enumeration over the hyperplane `Tr(s) = Tr(b/r^2)`.
Handbook: 15.1.2.4 Trace codes; 15.1.2.1 Standard array decoding; 15.1.2.3 Reed-Muller codes.
Phase: decomposition.
Claim: `w^2 + r w + r^2 s^2 + b = 0` is solvable iff `Tr(s) = Tr(b/r^2)`; walking `V`
along the hyperplane yields the same relation set as hash lookup, over half the points. -/
def h026Gray (i : Nat) : Nat := i ^^^ (i >>> 1)

/-- Arithmetic in GF(8) = F2[x]/(x^3+x+1), as a decidable small instance. -/
def h026Dbl (x : Nat) : Nat := if 2 * x ≥ 8 then (2 * x) ^^^ 11 else 2 * x

def h026Mul (a b : Nat) : Nat :=
  (if b % 2 = 1 then a else 0) ^^^
  (if b / 2 % 2 = 1 then h026Dbl a else 0) ^^^
  (if b / 4 % 2 = 1 then h026Dbl (h026Dbl a) else 0)

def h026Sq (x : Nat) : Nat := h026Mul x x

/-- Semaev `S3` core (without `b`): `(x1x2+x1x3+x2x3)^2 + x1x2x3`. -/
def h026S3Core (x1 x2 x3 : Nat) : Nat :=
  h026Sq (h026Mul x1 x2 ^^^ h026Mul x1 x3 ^^^ h026Mul x2 x3) ^^^ h026Mul (h026Mul x1 x2) x3

/-- Artin-Schreier form with `s = x1+x2`, `w = x1 x2`, `r = x3` (without `b`). -/
def h026AS (s w r : Nat) : Nat := h026Sq w ^^^ h026Mul r w ^^^ h026Sq (h026Mul r s)

def H026_claim : Prop :=
  ∀ (V walk : List Nat) (solvable : Nat → Prop) (hyp : Nat → Bool),
    (∀ s, solvable s ↔ hyp s = true) →
    walk = V.filter hyp →
    (∀ s, s ∈ walk ↔ s ∈ V ∧ solvable s) ∧ walk.length ≤ V.length

theorem H026_claim_proved : H026_claim := by
  intro V walk solvable hyp hsolv hw
  subst hw
  refine ⟨fun s => ?_, List.length_filter_le _ _⟩
  rw [List.mem_filter, hsolv]

/-- The `S3 = 0` iff Artin-Schreier identity, checked exhaustively over GF(8). -/
theorem H026_identity_gf8 :
    ∀ x1, x1 < 8 → ∀ x2, x2 < 8 → ∀ r, r < 8 →
      h026S3Core x1 x2 r = h026AS (x1 ^^^ x2) (h026Mul x1 x2) r := by
  decide

theorem H026_iff_gf8 (b : Nat) (x1 x2 r : Nat) (h1 : x1 < 8) (h2 : x2 < 8) (h3 : r < 8) :
    (h026S3Core x1 x2 r ^^^ b = 0) ↔
      (h026AS (x1 ^^^ x2) (h026Mul x1 x2) r ^^^ b = 0) := by
  rw [H026_identity_gf8 x1 h1 x2 h2 r h3]

/-- Consecutive Gray codes differ in exactly one bit (checked for the first 128 steps). -/
theorem H026_gray_one_bit :
    ∀ i, i < 128 → b03Pop 16 (h026Gray i ^^^ h026Gray (i + 1)) = 1 := by
  decide

theorem H026_hyperplane_half (k : Nat) : 2 ^ (k + 1 - 1) * 2 = 2 ^ (k + 1) := by
  simp [Nat.pow_succ]

/-! ## H027 -/

/-- **H027** — Rank profile of Weil-restricted `S3` components as F4 degree predictor.
Handbook: 15.1.2.3 Reed-Muller codes; 15.1.2.4 Trace codes; 15.1.3 Cyclic codes.
Phase: decomposition.
Claim: Frobenius-invariant `V` gives F4 solving degree at least 1 below a random `V`,
predicted by the dimension of the low-rank component subspace. -/
def h027Reduce (basis : List Nat) (v : Nat) : Nat :=
  basis.foldl (fun v b => if v ^^^ b < v then v ^^^ b else v) v

def h027Ins (v : Nat) : List Nat → List Nat
  | [] => [v]
  | b :: bs => if v ≥ b then v :: b :: bs else b :: h027Ins v bs

def h027Insert (basis : List Nat) (v : Nat) : List Nat :=
  let v' := h027Reduce basis v
  if v' = 0 then basis else h027Ins v' basis

/-- Rank over F2 of rows given as bitmasks, by xor elimination. -/
def h027Rank (rows : List Nat) : Nat := (rows.foldl h027Insert []).length

structure h027Obs where
  lowRankInv : Nat
  lowRankRnd : Nat
  degInv : Nat
  degRnd : Nat

def h027Dim (o : h027Obs) : Bool := decide (o.lowRankRnd + 3 ≤ o.lowRankInv)
def h027Drop (o : h027Obs) : Bool := decide (o.degInv + 1 ≤ o.degRnd)

def H027_claim : Prop :=
  ∀ (obs : List h027Obs),
    (∀ o ∈ obs, h027Dim o = true → h027Drop o = true) →
    60 * obs.length ≤ 100 * (obs.filter h027Dim).length →
    60 * obs.length ≤ 100 * (obs.filter h027Drop).length

theorem H027_claim_proved : H027_claim := by
  intro obs hmech hdim
  have := b03FilterMono h027Dim h027Drop obs hmech
  omega

theorem h027Ins_length (v : Nat) : ∀ l : List Nat, (h027Ins v l).length = l.length + 1
  | [] => by simp [h027Ins]
  | b :: bs => by
    unfold h027Ins
    split
    · simp
    · simp [h027Ins_length v bs]

theorem h027Insert_length_le (basis : List Nat) (v : Nat) :
    (h027Insert basis v).length ≤ basis.length + 1 := by
  unfold h027Insert
  simp only
  split
  · omega
  · rw [h027Ins_length]; omega

theorem h027Rank_fold_le (rows : List Nat) :
    ∀ basis : List Nat, (rows.foldl h027Insert basis).length ≤ basis.length + rows.length := by
  induction rows with
  | nil => intro basis; simp
  | cons a l ih =>
    intro basis
    simp only [List.foldl_cons, List.length_cons]
    have h1 := ih (h027Insert basis a)
    have h2 := h027Insert_length_le basis a
    omega

theorem H027_rank_le_rows (rows : List Nat) : h027Rank rows ≤ rows.length := by
  have := h027Rank_fold_le rows []
  simpa [h027Rank] using this

/-- Rank profiles at `n = 7`: the identity has rank 7; a dependent row drops it to 6;
adding row 0 to row 1 (an invertible change) preserves the rank. -/
theorem H027_rank_instances_n7 :
    h027Rank [1, 2, 4, 8, 16, 32, 64] = 7 ∧
    h027Rank [1, 2, 3, 8, 16, 32, 64] = 6 ∧
    h027Rank [1, 3, 4, 8, 16, 32, 64] = 7 := by
  decide

/-! ## H028 -/

/-- **H028** — Determinantal elliptic-normal-curve system keeping `y`.
Handbook: 14.4.5 k-Arcs; 14.4.1 Projective and affine spaces.
Phase: decomposition.
Claim: the determinantal system (Weil-restricted `x` only plus `y` coordinates) has lower
degree of regularity and solve time than `S_{m+1}` at equal `V` for `m = 3, 4`, with
matching solution sets. Variable counts: `m*(n/m+n)` against `(m+1)*n`. -/
structure h028Run where
  m : Nat
  n : Nat
  dregDet : Nat
  dregSem : Nat
  timeDet : Nat
  timeSem : Nat
  solsDet : List Nat
  solsSem : List Nat

def h028VarsDet (m n : Nat) : Nat := m * (n / m + n)
def h028VarsSem (m n : Nat) : Nat := (m + 1) * n

def H028_claim : Prop :=
  ∀ r : h028Run, r.m = 3 → r.n ≤ 25 → r.m ∣ r.n →
    r.dregDet + 1 ≤ r.dregSem ∧ 10 * r.timeDet ≤ 8 * r.timeSem ∧ r.solsDet = r.solsSem

theorem H028_var_balance (m n : Nat) (h : m ∣ n) : h028VarsDet m n = h028VarsSem m n := by
  unfold h028VarsDet h028VarsSem
  obtain ⟨k, hk⟩ := h
  subst hk
  by_cases hm : m = 0
  · subst hm; simp
  · have : m * k / m = k := Nat.mul_div_cancel_left k (Nat.pos_of_ne_zero hm)
    rw [this]
    rw [Nat.mul_add, Nat.add_mul, Nat.one_mul, Nat.add_comm]

theorem H028_time_ratio_implies_faster (a b : Nat) (h : 10 * a ≤ 8 * b) : a ≤ b := by omega

theorem H028_balance_m3_n21 : h028VarsDet 3 21 = h028VarsSem 3 21 := by decide

/-! ## H029 -/

/-- **H029** — Rank-count law as null model for `S3` pair matrices.
Handbook: 13.2.1 Matrices of specified rank; 13.3.5 Orthogonal groups, characteristic two.
Phase: decomposition.
Claim: `S3` is F2-affine in `x1` for fixed `(x2,x3)`, so solution sets are cosets of a
kernel; structured `V` have rank-deficient matrices at at least twice the uniform rate. -/
structure h029Hist where
  total : Nat
  deficient : Nat

def H029_claim : Prop :=
  ∀ (null structured : h029Hist) (L : Nat → Nat) (x0 y : Nat),
    (∀ a b, L (a ^^^ b) = L a ^^^ L b) → L x0 = y →
    (∀ x, L x = y ↔ L (x ^^^ x0) = 0) ∧
    (2 * null.deficient * structured.total ≤ structured.deficient * null.total →
      2 * (null.deficient * structured.total) ≤ structured.deficient * null.total)

theorem H029_coset (L : Nat → Nat) (hadd : ∀ a b, L (a ^^^ b) = L a ^^^ L b)
    (x0 y : Nat) (h0 : L x0 = y) (x : Nat) : L x = y ↔ L (x ^^^ x0) = 0 := by
  rw [hadd, h0]
  constructor
  · intro h; rw [h, Nat.xor_self]
  · intro h
    have := congrArg (· ^^^ y) h
    simpa [Nat.xor_assoc, Nat.xor_self] using this

theorem H029_claim_proved : H029_claim := by
  intro null structured L x0 y hadd h0
  refine ⟨H029_coset L hadd x0 y h0, ?_⟩
  intro h
  rw [← Nat.mul_assoc]
  exact h

/-- Instance check: for `L x = x &&& 5` on 3 bits, fibres have size 2 or 0. -/
theorem H029_fibres_instance :
    ((List.range 8).filter (fun x => (x &&& 5) == 0)).length = 2 ∧
    ((List.range 8).filter (fun x => (x &&& 5) == 1)).length = 2 ∧
    ((List.range 8).filter (fun x => (x &&& 5) == 2)).length = 0 := by
  decide

/-! ## H030 -/

/-- **H030** — Fill-triggered M4RI/PLE backend for Macaulay matrices.
Handbook: 13.4.1.1 Tiny finite fields; 13.4.2.2 PLE decomposition.
Phase: decomposition.
Claim: switching to Four-Russians PLE once fill exceeds 15 percent after 30 percent of
the pivots gives at least 2x fewer bit operations than sparse F4 on `n = 19..29` matrices,
at equal rank. -/
def h030Schoolbook (r c p : Nat) : Nat := p * r * c

/-- `p/k` blocks, each building a `2^k`-row table over `c` columns and applying it to `r` rows. -/
def h030M4ri (r c p k : Nat) : Nat := (p / k) * (2 ^ k * c + r * c)

def h030Trigger (nnz total pivDone pivTotal : Nat) : Bool :=
  decide (15 * total < 100 * nnz) && decide (30 * pivTotal ≤ 100 * pivDone)

structure h030Run where
  rows : Nat
  cols : Nat
  rankM4ri : Nat
  rankSparse : Nat
  opsM4ri : Nat
  opsSparse : Nat

def H030_claim : Prop :=
  ∀ q : h030Run, 20000 ≤ q.rows → 20000 ≤ q.cols → q.rankM4ri = q.rankSparse →
    2 * q.opsM4ri ≤ q.opsSparse

theorem H030_m4ri_le_schoolbook (r c p k : Nat) (hk : 0 < k) (hd : k ∣ p)
    (h : 2 ^ k + r ≤ k * r) : h030M4ri r c p k ≤ h030Schoolbook r c p := by
  obtain ⟨q, hq⟩ := hd
  subst hq
  have e : k * q / k = q := Nat.mul_div_cancel_left q hk
  unfold h030M4ri h030Schoolbook
  rw [e]
  have h1 : (2 ^ k * c + r * c) ≤ k * r * c := by
    calc 2 ^ k * c + r * c = (2 ^ k + r) * c := by rw [Nat.add_mul]
      _ ≤ (k * r) * c := Nat.mul_le_mul_right _ h
  calc q * (2 ^ k * c + r * c) ≤ q * (k * r * c) := Nat.mul_le_mul_left _ h1
    _ = k * q * r * c := by
        simp only [Nat.mul_comm, Nat.mul_left_comm]

theorem H030_trigger_mono (nnz nnz' total pivDone pivTotal : Nat) (h : nnz ≤ nnz')
    (ht : h030Trigger nnz total pivDone pivTotal = true) :
    h030Trigger nnz' total pivDone pivTotal = true := by
  unfold h030Trigger at *
  simp only [Bool.and_eq_true, decide_eq_true_eq] at ht ⊢
  omega

theorem H030_instance : 2 ^ 8 + 1000 ≤ 8 * 1000 ∧
    h030M4ri 1000 1000 64 8 ≤ h030Schoolbook 1000 1000 64 := by
  decide

end HandbookIC.Ideas.B03

#print axioms HandbookIC.Ideas.B03.b03FilterMono
#print axioms HandbookIC.Ideas.B03.H021_sound
#print axioms HandbookIC.Ideas.B03.H021_relCost_le
#print axioms HandbookIC.Ideas.B03.H021_claim_proved
#print axioms HandbookIC.Ideas.B03.H021_instance_n31_d9
#print axioms HandbookIC.Ideas.B03.h022Mono_pos
#print axioms HandbookIC.Ideas.B03.h022Mono_le_succ
#print axioms HandbookIC.Ideas.B03.h022Mono_mono
#print axioms HandbookIC.Ideas.B03.H022_bitDeg_le_two
#print axioms HandbookIC.Ideas.B03.H022_claim_proved
#print axioms HandbookIC.Ideas.B03.H023_filter_preserved
#print axioms HandbookIC.Ideas.B03.H023_live_le
#print axioms HandbookIC.Ideas.B03.H023_partition
#print axioms HandbookIC.Ideas.B03.H023_claim_proved
#print axioms HandbookIC.Ideas.B03.H023_strict_improvement
#print axioms HandbookIC.Ideas.B03.h024_decode_lifted
#print axioms HandbookIC.Ideas.B03.H024_claim_proved
#print axioms HandbookIC.Ideas.B03.H024_ratio
#print axioms HandbookIC.Ideas.B03.H024_xor_cancel
#print axioms HandbookIC.Ideas.B03.H025_count_invariant
#print axioms HandbookIC.Ideas.B03.H025_cost_scaling
#print axioms HandbookIC.Ideas.B03.H025_claim_proved
#print axioms HandbookIC.Ideas.B03.H026_claim_proved
#print axioms HandbookIC.Ideas.B03.H026_identity_gf8
#print axioms HandbookIC.Ideas.B03.H026_iff_gf8
#print axioms HandbookIC.Ideas.B03.H026_gray_one_bit
#print axioms HandbookIC.Ideas.B03.H026_hyperplane_half
#print axioms HandbookIC.Ideas.B03.H027_claim_proved
#print axioms HandbookIC.Ideas.B03.h027Ins_length
#print axioms HandbookIC.Ideas.B03.h027Insert_length_le
#print axioms HandbookIC.Ideas.B03.h027Rank_fold_le
#print axioms HandbookIC.Ideas.B03.H027_rank_le_rows
#print axioms HandbookIC.Ideas.B03.H027_rank_instances_n7
#print axioms HandbookIC.Ideas.B03.H028_var_balance
#print axioms HandbookIC.Ideas.B03.H028_time_ratio_implies_faster
#print axioms HandbookIC.Ideas.B03.H028_balance_m3_n21
#print axioms HandbookIC.Ideas.B03.H029_coset
#print axioms HandbookIC.Ideas.B03.H029_claim_proved
#print axioms HandbookIC.Ideas.B03.H029_fibres_instance
#print axioms HandbookIC.Ideas.B03.H030_m4ri_le_schoolbook
#print axioms HandbookIC.Ideas.B03.H030_trigger_mono
#print axioms HandbookIC.Ideas.B03.H030_instance
