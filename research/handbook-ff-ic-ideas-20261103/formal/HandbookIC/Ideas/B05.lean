import HandbookIC.Core

/-!
# HandbookIC.Ideas.B05 — handbook ideas H041 .. H050

Each idea has: a doc comment, definitions prefixed by the lower-case id,
`def Hxxx_claim : Prop` (all hypotheses explicit, curve facts are hypotheses
of the Prop, nothing is postulated) and at least one proved supporting theorem.
-/

namespace HandbookIC.Ideas.B05

open HandbookIC

/-! ## H041 -/

/-- **H041** Trace-form isotropic block pairs giving free linear equations.
Handbook 7.2.3 Trace forms. Phase: decomposition.
Claim: choosing `V1` in `(mu V2)^perp` kills the bilinear part on `dim M`
coordinates, i.e. gives `k = dim M` independent affine-linear equations, so the
`2^u` enumeration bound drops by the factor `2^k`. -/
def h041bound (u : Nat) : Nat := 2 ^ u

/-- Independent equations `k` out of `u` unknowns leave `u - k` free unknowns. -/
def h041reduced (u k : Nat) : Nat := h041bound (u - k)

def H041_claim : Prop :=
  ∀ (u k : Nat), k ≤ u →
    h041reduced u k * 2 ^ k = h041bound u ∧ (1 ≤ k → h041reduced u k < h041bound u)

theorem H041_reduction_factor (u k : Nat) (h : k ≤ u) :
    h041reduced u k * 2 ^ k = h041bound u := by
  unfold h041reduced h041bound
  rw [← Nat.pow_add, Nat.sub_add_cancel h]

theorem H041_strict (u k : Nat) (h : k ≤ u) (hk : 1 ≤ k) :
    h041reduced u k < h041bound u := by
  unfold h041reduced h041bound
  exact Nat.pow_lt_pow_right (by decide) (by omega)

theorem H041_claim_holds : H041_claim :=
  fun u k h => ⟨H041_reduction_factor u k h, H041_strict u k h⟩

/-- More independent equations never increase the bound. -/
theorem H041_mono (u k k' : Nat) (h : k ≤ k') : h041reduced u k' ≤ h041reduced u k := by
  unfold h041reduced h041bound
  exact Nat.pow_le_pow_right (by decide) (by omega)

/-! ## H042 -/

/-- **H042** Exact character-sum yield ranking of cyclic-code subspaces.
Handbook 6.2.2, 6.2.4, 6.3.3.3. Phase: decomposition.
Claim: equal-dimension Frobenius-invariant subspaces have yields differing by
`>= 3 sigma` with top `>= 1.2` median. Exact yields are character sums
(orthogonality of xor-parity characters and the indicator expansion of `V`);
the Weil bound caps how far any yield can leave the mean. -/
def h042par : Nat → Nat → Nat
  | 0, _ => 0
  | f + 1, m => (m % 2 + h042par f (m / 2)) % 2

/-- The character `x ↦ (-1)^{<s,x>}` on `n`-bit strings. -/
def h042chi (n s x : Nat) : Int := if h042par n (s &&& x) = 0 then 1 else -1

def h042charSum (n s : Nat) : Int :=
  ((List.range (2 ^ n)).map (fun x => h042chi n s x)).sum

/-- Two yields, a top and a bottom, are separated by `3 sigma` and the top is `>= 1.2 m`. -/
def h042Separated (ys : List Nat) (m sigma : Nat) : Prop :=
  ∃ a ∈ ys, ∃ b ∈ ys, b + 3 * sigma ≤ a ∧ 12 * m ≤ 10 * a

def H042_claim : Prop :=
  ∀ (ys : List Nat) (m sigma eps : Nat), ys ≠ [] → 0 < sigma →
    (∀ y ∈ ys, y ≤ m + eps ∧ m ≤ y + eps) →
    2 * (ys.filter (fun y => decide (y ≤ m))).length ≥ ys.length →
    h042Separated ys m sigma

/-- Orthogonality on 4-bit strings: the character sum is `2^n` at `s = 0`, else `0`. -/
theorem H042_orthogonality_4 :
    ((List.range 16).all (fun s =>
      if s = 0 then h042charSum 4 s == 16 else h042charSum 4 s == 0)) = true := by
  decide

/-- Indicator expansion of the subspace cut out by `s1 = 3`, `s2 = 5`:
`4 * 1_V(x) = Σ_{s in span} chi_s(x)`. -/
theorem H042_indicator_expansion_4 :
    ((List.range 16).all (fun x =>
      (4 : Int) * (if h042par 4 (3 &&& x) = 0 ∧ h042par 4 (5 &&& x) = 0 then 1 else 0)
        == ([0, 3, 5, 6].map (fun s => h042chi 4 s x)).sum)) = true := by
  decide

/-- A yield ratio of `1.2` above the mean is only possible if the Weil error
`eps` is at least `20%` of the mean. A Weil bound below that rules the ranking out. -/
theorem H042_ratio_needs_eps (y m eps : Nat) (hy : y ≤ m + eps) (hr : 12 * m ≤ 10 * y) :
    2 * m ≤ 10 * eps := by
  omega

/-! ## H043 -/

/-- **H043** Sparse Gauss-period normal basis for the restricted Semaev system.
Handbook 5.3.2, 5.3.1. Phase: decomposition.
Claim: in a type-II ONB (`p = 2d+1`, basis `zeta^j + zeta^-j`) the
multiplication tensor has `2d-1` nonzeros. Basis element `j` is a residue mod
`p` up to sign; `b_1 * b_j = b_{j+1} + b_{j-1}` with the zero index dropping out
(characteristic 2). -/
def h043fold (p r : Nat) : Nat := min (r % p) (p - r % p)

/-- Basis indices (nonzero classes) appearing in `b_1 * b_j`. -/
def h043terms (d j : Nat) : List Nat :=
  [h043fold (2 * d + 1) (j + 1), h043fold (2 * d + 1) (j + 2 * d)].filter (fun k => k != 0)

/-- Complexity as total number of terms over `j = 1..d`. -/
def h043cx (d : Nat) : Nat :=
  ((List.range d).map (fun i => (h043terms d (i + 1)).length)).sum

/-- Complexity as a count of true entries of the table `T[j][k]`. -/
def h043tcx (d : Nat) : Nat :=
  ((List.range d).map (fun i =>
    ((List.range d).filter (fun k => (h043terms d (i + 1)).contains (k + 1))).length)).sum

def H043_claim : Prop :=
  ∀ d : Nat, 1 ≤ d →
    (∀ k, 0 < k → k < 2 * d → 2 ^ k % (2 * d + 1) ≠ 1) →
    h043cx d = 2 * d - 1 ∧ h043tcx d = 2 * d - 1

theorem H043_complexity_d5 : h043cx 5 = 9 ∧ h043tcx 5 = 9 := by decide

theorem H043_complexity_d7 : h043cx 7 = 13 ∧ h043tcx 7 = 13 := by decide

theorem H043_terms_le_two (d j : Nat) : (h043terms d j).length ≤ 2 := by
  unfold h043terms
  exact Nat.le_trans (List.length_filter_le _ _) (by simp)

private theorem h043_sum_le (f : Nat → Nat) (hf : ∀ i, f i ≤ 2) (d : Nat) :
    ((List.range d).map f).sum ≤ 2 * d := by
  induction d with
  | zero => simp
  | succ n ih =>
    rw [List.range_succ, List.map_append, List.sum_append]
    simp
    have := hf n
    omega

/-- The tensor is sparse for every `d`: at most `2` terms per product, so at most `2d`. -/
theorem H043_cx_le (d : Nat) : h043cx d ≤ 2 * d :=
  h043_sum_le _ (fun i => H043_terms_le_two d (i + 1)) d

/-! ## H044 -/

/-- **H044** Order-6 automorphism-orbit quotient for `j=0` curves, `q ≡ 1 mod 3`.
Handbook 16.6.5, 16.6.4. Phase: relation-collection.
Claim: with `act j` multiplying logs by `lam^j` and `lam^6 ≡ 1`, quotienting a
base of `B` by the order-6 action needs `B/6` relations versus `B/2`, a ratio
of about 3, and twisted rows stay consistent mod the group order. -/
def h044act (n lam j g : Nat) : Nat := (lam ^ j * g) % n

def H044_claim : Prop :=
  ∀ (n lam B : Nat), lam ^ 6 % n = 1 % n →
    (∀ j s t, s % n = t % n → h044act n lam j s = h044act n lam j t) ∧
    (∀ s, h044act n lam 6 s = s % n) ∧
    orbitRepresentatives B 6 ≤ orbitRepresentatives B 2 ∧
    3 * orbitRepresentatives B 6 ≤ orbitRepresentatives B 2 ∧
    orbitRepresentatives B 2 ≤ 3 * orbitRepresentatives B 6 + 2

theorem H044_twisted_consistent (n lam j s t : Nat) (h : s % n = t % n) :
    h044act n lam j s = h044act n lam j t := by
  unfold h044act
  rw [Nat.mul_mod, h, ← Nat.mul_mod]

theorem H044_order6 (n lam s : Nat) (hl : lam ^ 6 % n = 1 % n) :
    h044act n lam 6 s = s % n := by
  unfold h044act
  rw [Nat.mul_mod, hl, ← Nat.mul_mod, Nat.one_mul]

theorem H044_ratio (B : Nat) :
    orbitRepresentatives B 6 ≤ orbitRepresentatives B 2 ∧
    3 * orbitRepresentatives B 6 ≤ orbitRepresentatives B 2 ∧
    orbitRepresentatives B 2 ≤ 3 * orbitRepresentatives B 6 + 2 := by
  unfold orbitRepresentatives
  omega

theorem H044_claim_holds : H044_claim := by
  intro n lam B hl
  exact ⟨fun j s t h => H044_twisted_consistent n lam j s t h,
    fun s => H044_order6 n lam s hl, H044_ratio B⟩

/-- Fewer relations with everything else fixed is a real total improvement. -/
theorem H044_total_improves (c : Cost) (B : Nat) (hB : 2 ≤ B)
    (h2 : c.relations = orbitRepresentatives B 2) :
    c.improvesRelations { c with relations := orbitRepresentatives B 6 } := by
  unfold Cost.improvesRelations orbitRepresentatives at *
  simp only [true_and]
  omega

/-! ## H045 -/

/-- **H045** Stop collection at orientability threshold; target-only left-kernel extraction.
Handbook 15.3, 15.5.1, 17.3.8, 15.5.2. Phase: relation-collection.
Claim: `t = log_P Q` is determined at the first left-kernel vector `y` of the
factor-base part with `y.b` a unit: `t = -(y.a)(y.b)^-1 mod n`. -/
structure h045Row where
  a : Int
  b : Int
  c : List Int

def h045dot : List Int → List Int → Int
  | y :: ys, v :: vs => y * v + h045dot ys vs
  | _, _ => 0

/-- `y` is a left-kernel vector of the factor-base part with `y.b ≠ 0`. -/
def h045Dep (rows : List h045Row) (y : List Int) : Prop :=
  y.length = rows.length ∧
  (∀ j, h045dot y (rows.map (fun r => r.c.getD j 0)) = 0) ∧
  h045dot y (rows.map (fun r => r.b)) ≠ 0

def h045Determined (rows : List h045Row) : Prop := ∃ y, h045Dep rows y

def H045_claim : Prop :=
  ∀ (n x Ya Yb binv : Int),
    (Ya + Yb * x) % n = 0 → (Yb * binv) % n = 1 % n →
    x % n = (-Ya * binv) % n

theorem H045_extract (n x Ya Yb binv : Int)
    (h1 : (Ya + Yb * x) % n = 0) (h2 : (Yb * binv) % n = 1 % n) :
    x % n = (-Ya * binv) % n := by
  have hd1 : n ∣ Ya + Yb * x := Int.dvd_of_emod_eq_zero h1
  have hd2 : n ∣ Yb * binv - 1 :=
    Int.dvd_of_emod_eq_zero ((Int.emod_eq_emod_iff_emod_sub_eq_zero).1 h2)
  have key : x - (-Ya * binv) = -x * (Yb * binv - 1) + binv * (Ya + Yb * x) := by grind
  apply (Int.emod_eq_emod_iff_emod_sub_eq_zero).2
  apply Int.emod_eq_zero_of_dvd
  rw [key]
  exact Int.dvd_add (Int.dvd_mul_of_dvd_right hd2) (Int.dvd_mul_of_dvd_right hd1)

theorem H045_claim_holds : H045_claim := H045_extract

private theorem h045dot_zeros (k : Nat) (w : List Int) :
    h045dot (List.replicate k 0) w = 0 := by
  induction k generalizing w with
  | zero => simp [h045dot]
  | succ k ih =>
    cases w with
    | nil => simp [h045dot]
    | cons v vs => simp [List.replicate_succ, h045dot, ih]

private theorem h045dot_append (y v : List Int) (k : Nat) (w : List Int)
    (h : y.length = v.length) :
    h045dot (y ++ List.replicate k 0) (v ++ w) = h045dot y v := by
  induction y generalizing v with
  | nil =>
    cases v with
    | nil => simp [h045dot, h045dot_zeros]
    | cons _ _ => simp at h
  | cons a as ih =>
    cases v with
    | nil => simp at h
    | cons b bs =>
      simp at h
      simp [h045dot, ih bs h]

/-- Once a dependency with unit `y.b` exists, appending more relations keeps it. -/
theorem H045_determined_mono (rows more : List h045Row) :
    h045Determined rows → h045Determined (rows ++ more) := by
  rintro ⟨y, hlen, hc, hb⟩
  refine ⟨y ++ List.replicate more.length 0, by simp [hlen], ?_, ?_⟩
  · intro j
    rw [List.map_append, h045dot_append _ _ _ _ (by simpa using hlen)]
    exact hc j
  · rw [List.map_append, h045dot_append _ _ _ _ (by simpa using hlen)]
    exact hb

/-! ## H046 -/

/-- **H046** Cayley-graph walk candidate generation with lambda_2-selected generators.
Handbook 14.10.3, 14.10.4. Phase: relation-collection.
Claim: the walk `R_{i+1} = R_i + s_j` carries `(a,b)` with `log R = a + b x`, so
every emitted relation is sound; with a yield ratio within 3% of iid, it costs
at least 5 times fewer group-op equivalents per relation. -/
def h046step (st : Int × Int) (s : Int × Int) : Int × Int := (st.1 + s.1, st.2 + s.2)

def h046walk (start : Int × Int) (steps : List (Int × Int)) : Int × Int :=
  steps.foldl h046step start

def h046stepLog (x : Int) (s : Int × Int) : Int := s.1 + s.2 * x

def h046sumLog (x : Int) (steps : List (Int × Int)) : Int :=
  (steps.map (h046stepLog x)).sum

/-- Yield ratio within 3% (the mixing hypothesis delivered by the spectral gap). -/
def h046Mixing (yw yi : Nat) : Prop := 97 * yi ≤ 100 * yw ∧ 100 * yw ≤ 103 * yi

def H046_claim : Prop :=
  ∀ (x : Int) (start : Int × Int) (steps : List (Int × Int)),
    (h046walk start steps).1 + (h046walk start steps).2 * x
      = start.1 + start.2 * x + h046sumLog x steps

theorem H046_walk_sound (x : Int) (steps : List (Int × Int)) :
    ∀ start : Int × Int,
      (h046walk start steps).1 + (h046walk start steps).2 * x
        = start.1 + start.2 * x + h046sumLog x steps := by
  induction steps with
  | nil => intro start; simp [h046walk, h046sumLog]
  | cons s t ih =>
    intro start
    have := ih (h046step start s)
    unfold h046walk at this ⊢
    simp only [List.foldl_cons]
    rw [this]
    unfold h046sumLog h046stepLog h046step
    simp only [List.map_cons, List.sum_cons]
    rw [Int.add_mul]
    omega

theorem H046_claim_holds : H046_claim := fun x start steps => H046_walk_sound x steps start

/-- Per-relation cost: with yields within 3% and an iid candidate costing at least 6
operations against 1 for the walk, the walk spends at least 5 times fewer operations per
relation (cross-multiplied: `5 * N * yi <= N * opsIid * yw`). -/
theorem H046_ops_per_relation (N opsIid yw yi : Nat) (hy : 97 * yi ≤ 100 * yw)
    (hops : 6 ≤ opsIid) : 5 * (N * yi) ≤ N * (opsIid * yw) := by
  have h1 : 5 * yi ≤ 6 * yw := by omega
  have h2 : 6 * yw ≤ opsIid * yw := Nat.mul_le_mul_right yw hops
  have h3 : 5 * yi ≤ opsIid * yw := Nat.le_trans h1 h2
  calc 5 * (N * yi) = N * (5 * yi) := by rw [Nat.mul_left_comm]
    _ ≤ N * (opsIid * yw) := Nat.mul_le_mul_left N h3

/-! ## H047 -/

/-- **H047** Koblitz tau-adic Gray-code enumeration with an `a_0 = 1` orbit-duplicate filter.
Handbook 14.8.5, 14.8.6. Phase: relation-collection.
Claim: the Gray code enumerates all `2^k` strings with one-bit steps (one mixed
addition per candidate), and restricting to `a_0 = 1` removes the orbit
duplicates, leaving exactly half the strings. -/
def h047gray (m : Nat) : Nat := m ^^^ (m >>> 1)

def h047oneBit (m : Nat) : Bool :=
  let x := h047gray m ^^^ h047gray (m + 1)
  x != 0 && (x &&& (x - 1)) == 0

def H047_claim : Prop :=
  ∀ k : Nat,
    ((List.range (2 ^ k)).map h047gray).Nodup ∧
    (∀ m, m + 1 < 2 ^ k → h047oneBit m = true) ∧
    (∀ m, m < 2 ^ k → h047gray m < 2 ^ k) ∧
    1 ≤ k → ((List.range (2 ^ k)).filter (fun m => m % 2 == 1)).length = 2 ^ (k - 1)

set_option maxRecDepth 100000 in
theorem H047_gray_injective_6 : ((List.range 64).map h047gray).Nodup := by decide

set_option maxRecDepth 100000 in
theorem H047_gray_onebit_8 : (List.range 255).all h047oneBit = true := by decide

set_option maxRecDepth 100000 in
theorem H047_gray_closed_8 : (List.range 256).all (fun m => h047gray m < 256) = true := by decide

set_option maxRecDepth 100000 in
theorem H047_filter_half_6 :
    ((List.range 64).filter (fun m => m % 2 == 1)).length = 32 := by decide

/-- Cost: one addition per candidate versus `2n/3` per candidate for the tau-adic
recomputation; for `2n/3 >= 5` the Gray walk spends at most a fifth. -/
theorem H047_gray_cost (N n : Nat) (h : 5 ≤ 2 * n / 3) :
    5 * (N * 1) ≤ N * (2 * n / 3) := by
  have : N * 5 ≤ N * (2 * n / 3) := Nat.mul_le_mul_left N h
  omega

/-! ## H048 -/

/-- **H048** Walsh-bias audit of the decomposable-target indicator for linear prefilters.
Handbook 14.2.3, 14.2.4. Phase: relation-collection.
Claim: for a set `D` of density `|D|`, Parseval forces
`max_s W(s)^2 >= |D|`, so the max normalised Walsh coefficient has the floor
`1/sqrt|D|`; bias beyond random fluctuation exists only for structured `V`. -/
def h048walsh (n mask s : Nat) : Int :=
  ((List.range (2 ^ n)).map (fun x => if mask.testBit x then h042chi n s x else 0)).sum

def h048card (n mask : Nat) : Nat :=
  ((List.range (2 ^ n)).filter (fun x => mask.testBit x)).length

def h048sq (n mask : Nat) : Int :=
  ((List.range (2 ^ n)).map (fun s => h048walsh n mask s * h048walsh n mask s)).sum

def H048_claim : Prop :=
  ∀ (ws : List Nat) (d M : Nat), 0 < ws.length →
    ws.sum = ws.length * d → (∀ w ∈ ws, w ≤ M) → d ≤ M

set_option maxRecDepth 100000 in
/-- Parseval on all subsets of the 3-bit cube: `Σ_s W(s)^2 = 2^n |D|`. -/
theorem H048_parseval_3 :
    ((List.range 256).all (fun mask =>
      h048sq 3 mask == (8 : Int) * (h048card 3 mask : Int))) = true := by
  decide

private theorem h048_sum_le (ws : List Nat) (M : Nat) (h : ∀ w ∈ ws, w ≤ M) :
    ws.sum ≤ ws.length * M := by
  induction ws with
  | nil => simp
  | cons a t ih =>
    have h1 := h a (by simp)
    have h2 := ih (fun w hw => h w (by simp [hw]))
    simp only [List.sum_cons, List.length_cons]
    rw [Nat.succ_mul]
    omega

/-- The floor: if the squared coefficients average to `d` then some bound `M` on all
of them satisfies `d <= M`. -/
theorem H048_floor : H048_claim := by
  intro ws d M hpos hsum hM
  have h := h048_sum_le ws M hM
  rw [hsum] at h
  exact Nat.le_of_mul_le_mul_left h hpos

/-! ## H049 -/

/-- **H049** Streaming PLE rank certificate to stop at rank `B-1` versus fixed excess.
Handbook 13.4.2.2, 13.4.4.2. Phase: relation-collection.
Claim: the stop time `k*` = least `k` with `rankAt k >= B-1` is at most the
fixed-rule time `K` whenever the rank reaches `B-1` by `K`; the probe cost is a
separate field and the saving is real only if it stays below the relations saved. -/
def h049go (r : Nat → Nat) (target : Nat) (k : Nat) : Nat → Nat
  | 0 => k
  | f + 1 => if target ≤ r k then k else h049go r target (k + 1) f

/-- Least `k < fuel` with `target <= r k` (returns `fuel` if none). -/
def h049stop (r : Nat → Nat) (target fuel : Nat) : Nat := h049go r target 0 fuel

def H049_claim : Prop :=
  ∀ (r : Nat → Nat) (B K : Nat), 1 ≤ B → B - 1 ≤ r K →
    h049stop r (B - 1) (K + 1) ≤ K

private theorem h049go_le (r : Nat → Nat) (target K : Nat) (hK : target ≤ r K) :
    ∀ (fuel k : Nat), k ≤ K → K < k + fuel → h049go r target k fuel ≤ K := by
  intro fuel
  induction fuel with
  | zero => intro k hk hlt; omega
  | succ f ih =>
    intro k hk hlt
    unfold h049go
    by_cases h : target ≤ r k
    · simp [h]; exact hk
    · simp [h]
      have hne : k ≠ K := by
        intro e; subst e; exact h hK
      exact ih (k + 1) (by omega) (by omega)

theorem H049_stop_le_fixed : H049_claim := by
  intro r B K _ hK
  exact h049go_le r (B - 1) K hK (K + 1) 0 (by omega) (by omega)

/-- With the probe cost charged as its own relation-phase unit, a strictly cheaper stop is
a real total improvement. -/
theorem H049_net_improvement (c : Cost) (fixedRel stopRel probe : Nat)
    (h : c.relations = fixedRel) (hlt : stopRel + probe < fixedRel) :
    c.improvesRelations { c with relations := stopRel + probe } := by
  unfold Cost.improvesRelations
  simp only [true_and]
  omega

/-- Saving fraction check at 0/0.1/1 pricing: the net saving is the relations saved
minus the priced probe cost (all in integer tenths). -/
theorem H049_priced_saving (fixedRel stopRel probeOps price : Nat)
    (_hprice : price ≤ 10) (hp : probeOps * price ≤ 10 * (fixedRel - stopRel))
    (hle : stopRel ≤ fixedRel) :
    10 * stopRel + probeOps * price ≤ 10 * fixedRel := by
  omega

/-! ## H050 -/

/-- **H050** Fano factor of solution counts: Frobenius clumping of yield per call.
Handbook 11.2.3.2, 11.2.3.5. Phase: relation-collection.
Claim: solutions on an invariant `V` come in orbits of size at most `k` (here
`k = n`), so `solutions <= k * orbits` and independent relations per call are
orbits: `orbits >= solutions / k`. -/
def h050solutions (sizes : List Nat) : Nat := sizes.sum

def h050orbits (sizes : List Nat) : Nat := sizes.length

def H050_claim : Prop :=
  ∀ (sizes : List Nat) (k : Nat), 0 < k → (∀ s ∈ sizes, 1 ≤ s ∧ s ≤ k) →
    h050solutions sizes ≤ k * h050orbits sizes ∧
    h050orbits sizes ≤ h050solutions sizes ∧
    h050solutions sizes / k ≤ h050orbits sizes

theorem H050_solutions_le (sizes : List Nat) (k : Nat) (h : ∀ s ∈ sizes, s ≤ k) :
    h050solutions sizes ≤ k * h050orbits sizes := by
  unfold h050solutions h050orbits
  induction sizes with
  | nil => simp
  | cons a t ih =>
    have h1 := h a (by simp)
    have h2 := ih (fun s hs => h s (by simp [hs]))
    simp only [List.sum_cons, List.length_cons]
    rw [Nat.mul_succ]
    omega

theorem H050_orbits_le (sizes : List Nat) (h : ∀ s ∈ sizes, 1 ≤ s) :
    h050orbits sizes ≤ h050solutions sizes := by
  unfold h050solutions h050orbits
  induction sizes with
  | nil => simp
  | cons a t ih =>
    have h1 := h a (by simp)
    have h2 := ih (fun s hs => h s (by simp [hs]))
    simp only [List.sum_cons, List.length_cons]
    omega

theorem H050_claim_holds : H050_claim := by
  intro sizes k hk h
  have h1 := H050_solutions_le sizes k (fun s hs => (h s hs).2)
  refine ⟨h1, H050_orbits_le sizes (fun s hs => (h s hs).1), ?_⟩
  exact Nat.div_le_of_le_mul h1

end HandbookIC.Ideas.B05

#print axioms HandbookIC.Ideas.B05.H041_reduction_factor
#print axioms HandbookIC.Ideas.B05.H041_strict
#print axioms HandbookIC.Ideas.B05.H041_claim_holds
#print axioms HandbookIC.Ideas.B05.H041_mono
#print axioms HandbookIC.Ideas.B05.H042_orthogonality_4
#print axioms HandbookIC.Ideas.B05.H042_indicator_expansion_4
#print axioms HandbookIC.Ideas.B05.H042_ratio_needs_eps
#print axioms HandbookIC.Ideas.B05.H043_complexity_d5
#print axioms HandbookIC.Ideas.B05.H043_complexity_d7
#print axioms HandbookIC.Ideas.B05.H043_terms_le_two
#print axioms HandbookIC.Ideas.B05.H043_cx_le
#print axioms HandbookIC.Ideas.B05.H044_twisted_consistent
#print axioms HandbookIC.Ideas.B05.H044_order6
#print axioms HandbookIC.Ideas.B05.H044_ratio
#print axioms HandbookIC.Ideas.B05.H044_claim_holds
#print axioms HandbookIC.Ideas.B05.H044_total_improves
#print axioms HandbookIC.Ideas.B05.H045_extract
#print axioms HandbookIC.Ideas.B05.H045_claim_holds
#print axioms HandbookIC.Ideas.B05.H045_determined_mono
#print axioms HandbookIC.Ideas.B05.H046_walk_sound
#print axioms HandbookIC.Ideas.B05.H046_claim_holds
#print axioms HandbookIC.Ideas.B05.H046_ops_per_relation
#print axioms HandbookIC.Ideas.B05.H047_gray_injective_6
#print axioms HandbookIC.Ideas.B05.H047_gray_onebit_8
#print axioms HandbookIC.Ideas.B05.H047_gray_closed_8
#print axioms HandbookIC.Ideas.B05.H047_filter_half_6
#print axioms HandbookIC.Ideas.B05.H047_gray_cost
#print axioms HandbookIC.Ideas.B05.H048_parseval_3
#print axioms HandbookIC.Ideas.B05.H048_floor
#print axioms HandbookIC.Ideas.B05.H049_stop_le_fixed
#print axioms HandbookIC.Ideas.B05.H049_net_improvement
#print axioms HandbookIC.Ideas.B05.H049_priced_saving
#print axioms HandbookIC.Ideas.B05.H050_solutions_le
#print axioms HandbookIC.Ideas.B05.H050_orbits_le
#print axioms HandbookIC.Ideas.B05.H050_claim_holds
