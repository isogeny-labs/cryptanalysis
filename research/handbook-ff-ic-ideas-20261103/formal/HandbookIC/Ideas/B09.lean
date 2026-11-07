import HandbookIC.Core

/-!
# HandbookIC.Ideas.B09 — handbook ideas H081 .. H090 (cost model, curve selection, hardware)

Each idea has: a doc comment, definitions prefixed by the lower-case id,
`def Hxxx_claim : Prop` (all hypotheses explicit; curve facts are hypotheses,
never postulated) and at least one proved supporting theorem.
-/

namespace HandbookIC.Ideas.B09

open HandbookIC

/-! ## Shared helpers -/

theorem b09_sum_const {β : Type} (l : List β) (c : Nat) :
    (l.map (fun _ => c)).sum = l.length * c := by
  induction l with
  | nil => simp
  | cons x l ih => simp [ih, Nat.succ_mul]; omega

/-! ## H081 -/

/-- H081: Correlation measure C_2 of the decomposability indicator along an additive sweep.
Handbook 10.4.5.3. ic_phase: cost-model.
Claim: generic shifts keep C_2 within a sqrt(L ln L) band, tau-multiple shifts on
Koblitz curves exceed it, so a model assuming the band everywhere understates variance. -/
def h081Sgn (a b : Bool) : Int := if a == b then 1 else -1

def h081Corr : List Bool → List Bool → Int
  | x :: xs, y :: ys => h081Sgn x y + h081Corr xs ys
  | _, _ => 0

def h081Dis : List Bool → List Bool → Nat
  | x :: xs, y :: ys => (if x == y then 0 else 1) + h081Dis xs ys
  | _, _ => 0

/-- Cyclic order-2 correlation of the indicator `d` at shift `t`. -/
def h081C2 (d : List Bool) (t : Nat) : Int := h081Corr d (d.rotateLeft t)

theorem H081_corr_identity (xs ys : List Bool) (h : xs.length = ys.length) :
    h081Corr xs ys = (xs.length : Int) - 2 * (h081Dis xs ys : Int) := by
  induction xs generalizing ys with
  | nil => cases ys <;> simp_all [h081Corr, h081Dis]
  | cons x xs ih =>
    cases ys with
    | nil => simp at h
    | cons y ys =>
      have := ih ys (by simpa using h)
      simp only [h081Corr, h081Dis, List.length_cons]
      rw [this]
      cases x <;> cases y <;> simp [h081Sgn] <;> omega

theorem H081_dis_le (xs ys : List Bool) : h081Dis xs ys ≤ xs.length := by
  induction xs generalizing ys with
  | nil => cases ys <;> simp [h081Dis]
  | cons x xs ih =>
    cases ys with
    | nil => simp [h081Dis]
    | cons y ys =>
      have := ih ys
      simp only [h081Dis, List.length_cons]
      split <;> omega

theorem H081_corr_abs_le (xs ys : List Bool) (h : xs.length = ys.length) :
    (h081Corr xs ys).natAbs ≤ xs.length := by
  have h1 := H081_corr_identity xs ys h
  have h2 := H081_dis_le xs ys
  omega

theorem b09_rotl_length (d : List Bool) (t : Nat) : (d.rotateLeft t).length = d.length := by
  by_cases h : d.length ≤ 1
  · simp [List.rotateLeft, h]
  · have : t % d.length < d.length := Nat.mod_lt _ (by omega)
    simp [List.rotateLeft, h]
    omega

theorem H081_C2_abs_le (d : List Bool) (t : Nat) : (h081C2 d t).natAbs ≤ d.length := by
  unfold h081C2
  exact H081_corr_abs_le d _ (b09_rotl_length d t).symm

def H081_claim : Prop :=
  ∀ (d : List Bool) (bound : Nat) (generic tau : List Nat),
    (∀ t ∈ generic, (h081C2 d t).natAbs ≤ bound) →
    (∃ t ∈ tau, bound < (h081C2 d t).natAbs) →
    ¬ (∀ t ∈ generic ++ tau, (h081C2 d t).natAbs ≤ bound)

theorem H081_claim_holds : H081_claim := by
  intro d bound generic tau _ ⟨t, ht, hlt⟩ hall
  have := hall t (List.mem_append_right _ ht)
  omega

/-! ## H082 -/

/-- H082: Multihomogeneous Bezout predictor of F4 time for split systems.
Handbook 7.1.3. ic_phase: cost-model.
Claim: a model driven by the block-degree product picks the best parameter whenever
time is monotone in the model (a measured correlation hypothesis). -/
def h082Prod : List Nat → Nat
  | [] => 1
  | d :: ds => d * h082Prod ds

/-- Blockwise domination of degree vectors. -/
inductive H082Le : List Nat → List Nat → Prop
  | nil : H082Le [] []
  | cons {a b : Nat} {as bs : List Nat} : a ≤ b → H082Le as bs → H082Le (a :: as) (b :: bs)

theorem H082_prod_mono {ds ds' : List Nat} (h : H082Le ds ds') :
    h082Prod ds ≤ h082Prod ds' := by
  induction h with
  | nil => exact Nat.le_refl _
  | cons h1 _ ih => exact Nat.mul_le_mul h1 ih

theorem H082_total_sum (c : Cost) :
    c.total = [c.factorBase, c.relations, c.linearAlgebra, c.descent].sum := by
  simp [Cost.total]; omega

def H082_claim : Prop :=
  ∀ (bmh time : Nat → Nat) (cands : List Nat) (c0 : Nat),
    c0 ∈ cands → (∀ c ∈ cands, bmh c0 ≤ bmh c) →
    (∀ a b, bmh a ≤ bmh b → time a ≤ time b) →
    ∀ c ∈ cands, time c0 ≤ time c

theorem H082_claim_holds : H082_claim := by
  intro bmh time cands c0 _ hmin hmono c hc
  exact hmono _ _ (hmin c hc)

/-! ## H083 -/

/-- H083: Variance-to-mean audit of decomposition counts.
Handbook 6.3.6.3-4. ic_phase: cost-model.
Claim: sums of exactly `m` base logs number `B^m`, and coverage by up to `m` terms is
monotone in `m` and bounded by the group order. -/
def h083Sums (L : List Nat) : Nat → List Nat
  | 0 => [0]
  | m + 1 => L.flatMap (fun l => (h083Sums L m).map (· + l))

def h083Reach (L : List Nat) : Nat → List Nat
  | 0 => [0]
  | m + 1 => h083Reach L m ++ L.flatMap (fun l => (h083Reach L m).map (· + l))

def h083Coverage (n : Nat) (L : List Nat) (m : Nat) : Nat :=
  (List.range n).countP (fun t => (h083Reach L m).any (fun s => s % n == t))

theorem H083_sums_length (L : List Nat) (m : Nat) :
    (h083Sums L m).length = L.length ^ m := by
  induction m with
  | zero => simp [h083Sums]
  | succ m ih =>
    simp only [h083Sums, List.length_flatMap, List.length_map, ih]
    rw [b09_sum_const, Nat.pow_succ, Nat.mul_comm]

theorem H083_coverage_step (n : Nat) (L : List Nat) (m : Nat) :
    h083Coverage n L m ≤ h083Coverage n L (m + 1) := by
  unfold h083Coverage
  apply List.countP_mono_left
  intro t _ hp
  simp only [h083Reach, List.any_append]
  simp [hp]

theorem H083_coverage_mono (n : Nat) (L : List Nat) {m m' : Nat} (h : m ≤ m') :
    h083Coverage n L m ≤ h083Coverage n L m' := by
  induction h with
  | refl => exact Nat.le_refl _
  | step _ ih => exact Nat.le_trans ih (H083_coverage_step n L _)

theorem H083_coverage_le (n : Nat) (L : List Nat) (m : Nat) :
    h083Coverage n L m ≤ n := by
  unfold h083Coverage
  have := List.countP_le_length (l := List.range n)
    (p := fun t => (h083Reach L m).any (fun s => s % n == t))
  simpa using this

def H083_claim : Prop :=
  ∀ (n : Nat) (L : List Nat) (m : Nat),
    (h083Sums L m).length = L.length ^ m ∧ h083Coverage n L m ≤ n ∧
    ∀ m', m ≤ m' → h083Coverage n L m ≤ h083Coverage n L m'

theorem H083_claim_holds : H083_claim := fun n L m =>
  ⟨H083_sums_length L m, H083_coverage_le n L m, fun _ h => H083_coverage_mono n L h⟩

/-! ## H084 -/

/-- H084: Koblitz twin-curve amortisation.
Handbook 16.4.1.3, 16.4.2.2. ic_phase: curve-selection.
Claim: if no solution is mixed, solutions partition into pure E_0 and pure E_1, so the total
is E0 + E1, and with an even split each instance gets total/2 relations. -/
def h084Count (ty : α → Nat) (k : Nat) (sols : List α) : Nat :=
  sols.countP (fun s => ty s == k)

theorem b09_smooth_true {α : Type} (xs : List α) :
    smoothCount xs (fun _ => true) = xs.length := by
  unfold smoothCount
  rw [List.filter_eq_self.mpr (fun _ _ => rfl)]

theorem H084_partition {α : Type} (ty : α → Nat) (sols : List α)
    (hmix : ∀ s ∈ sols, ty s = 0 ∨ ty s = 1) :
    sols.length = h084Count ty 0 sols + h084Count ty 1 sols := by
  induction sols with
  | nil => simp [h084Count]
  | cons s sols ih =>
    have ih' := ih (fun x hx => hmix x (List.mem_cons_of_mem s hx))
    have hs := hmix s List.mem_cons_self
    unfold h084Count at ih' ⊢
    rcases hs with h | h <;> simp [h] <;> omega

theorem H084_amortised {α : Type} (ty : α → Nat) (sols : List α)
    (hmix : ∀ s ∈ sols, ty s = 0 ∨ ty s = 1)
    (hsplit : h084Count ty 0 sols = h084Count ty 1 sols) :
    sols.length / 2 = h084Count ty 0 sols := by
  have := H084_partition ty sols hmix
  omega

def H084_claim : Prop :=
  ∀ (α : Type) (ty : α → Nat) (sols : List α),
    (∀ s ∈ sols, ty s = 0 ∨ ty s = 1) →
    smoothCount sols (fun _ => true) = h084Count ty 0 sols + h084Count ty 1 sols

theorem H084_claim_holds : H084_claim := by
  intro α ty sols hmix
  have := H084_partition ty sols hmix
  rw [b09_smooth_true]
  exact this

/-! ## H085 -/

/-- H085: Select GHS/Weil-descent covers by maximal rational-point count.
Handbook 14.8.3. ic_phase: curve-selection.
Claim: the number of g-subsets of N points is monotone in N, a surjective sum map onto
a class group of size J forces at least J sums. -/
def h085Choose : Nat → Nat → Nat
  | _, 0 => 1
  | 0, _ + 1 => 0
  | n + 1, k + 1 => h085Choose n k + h085Choose n (k + 1)

theorem H085_choose_step (n k : Nat) : h085Choose n k ≤ h085Choose (n + 1) k := by
  cases k with
  | zero => simp [h085Choose]
  | succ k => simp only [h085Choose]; omega

theorem H085_choose_mono (g : Nat) {N N' : Nat} (h : N ≤ N') :
    h085Choose N g ≤ h085Choose N' g := by
  induction h with
  | refl => exact Nat.le_refl _
  | step _ ih => exact Nat.le_trans ih (H085_choose_step _ g)

theorem H085_choose_small : h085Choose 5 2 = 10 ∧ h085Choose 8 3 = 56 := by decide

theorem H085_surj_card (J : Nat) (sums : List Nat) (key : Nat → Nat)
    (h : ∀ j, j < J → j ∈ sums.map key) : J ≤ sums.length := by
  have hsub : List.range J ⊆ sums.map key := by
    intro j hj
    exact h j (List.mem_range.mp hj)
  have := List.Nodup.length_le_of_subset (List.nodup_range) hsub
  simpa using this

def H085_claim : Prop :=
  ∀ (N1 N2 g c : Nat) (yield : Nat → Nat),
    N1 ≤ N2 → (∀ N, yield N = c * h085Choose N g) → yield N1 ≤ yield N2

theorem H085_claim_holds : H085_claim := by
  intro N1 N2 g c yield h hy
  rw [hy, hy]
  exact Nat.mul_le_mul (Nat.le_refl _) (H085_choose_mono g h)

/-! ## H086 -/

/-- H086: Invariant-dimension screen with rotation-only membership.
Handbook 13.2.3-4. ic_phase: curve-selection.
Claim: a rotation-closed set of bit vectors is a union of rotation orbits, hence with
orbit size <= n the set has at most n * (number of orbit keys) elements. -/
def h086Rot (v : List Bool) : List Bool := v.rotateLeft 1

def h086Iter : Nat → List Bool → List Bool
  | 0, v => v
  | k + 1, v => h086Rot (h086Iter k v)

def h086ShiftClosed (S : List Bool → Prop) : Prop := ∀ v, S v → S (h086Rot v)

theorem H086_orbit_closed (S : List Bool → Prop) (hS : h086ShiftClosed S) (v : List Bool)
    (hv : S v) (k : Nat) : S (h086Iter k v) := by
  induction k with
  | zero => exact hv
  | succ k ih => exact hS _ ih

theorem H086_countP_or {α : Type} (p q : α → Bool) (xs : List α) :
    xs.countP (fun a => p a || q a) ≤ xs.countP p + xs.countP q := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    simp only [List.countP_cons]
    by_cases hp : p x = true <;> by_cases hq : q x = true <;> simp [hp, hq] <;> omega

theorem H086_countP_reps {α : Type} (key : α → Nat) (n : Nat) (V : List α)
    (hb : ∀ r, V.countP (fun a => key a == r) ≤ n) (reps : List Nat) :
    V.countP (fun a => reps.contains (key a)) ≤ reps.length * n := by
  induction reps with
  | nil => simp
  | cons r reps ih =>
    have h1 := H086_countP_or (fun a => key a == r) (fun a => reps.contains (key a)) V
    have h2 := hb r
    have h3 : V.countP (fun a => (r :: reps).contains (key a))
        ≤ V.countP (fun a => (key a == r) || reps.contains (key a)) := by
      apply List.countP_mono_left
      intro a _ ha
      simp only [List.contains_cons] at ha
      simpa [BEq.comm] using ha
    simp only [List.length_cons, Nat.succ_mul]
    omega

theorem H086_card_le {α : Type} (key : α → Nat) (n : Nat) (V : List α) (reps : List Nat)
    (hcov : ∀ a ∈ V, key a ∈ reps) (hb : ∀ r, V.countP (fun a => key a == r) ≤ n) :
    smoothCount V (fun _ => true) ≤ n * reps.length := by
  have h := H086_countP_reps key n V hb reps
  have h2 : V.countP (fun a => reps.contains (key a)) = V.length :=
    List.countP_eq_length.mpr (fun a ha => by simpa using hcov a ha)
  rw [b09_smooth_true, Nat.mul_comm]
  omega

def H086_claim : Prop :=
  ∀ (n : Nat) (V : List (List Bool)) (reps : List Nat) (key : List Bool → Nat),
    (∀ a ∈ V, key a ∈ reps) → (∀ r, V.countP (fun a => key a == r) ≤ n) →
    smoothCount V (fun _ => true) ≤ n * reps.length

theorem H086_claim_holds : H086_claim := fun n V reps key hc hb =>
  H086_card_le key n V reps hc hb

/-! ## H087 -/

/-- H087: Volcano ascent to a j=0 or 1728 crater for an Aut-6 / Aut-4 quotient.
Handbook 12.2.3, 12.2.8, 12.2.9. ic_phase: curve-selection.
Claim: quotienting by Aut of order 6 equals quotienting by 2 then 3 (and 4 = 2*2), and an
isogeny with exponent-side degree `d` transports DLP relations when its image group order
divides the source order. -/
theorem H087_orbit_six (N : Nat) :
    orbitRepresentatives N 6 = orbitRepresentatives (orbitRepresentatives N 2) 3 := by
  unfold orbitRepresentatives
  rw [Nat.div_div_eq_div_mul]

theorem H087_orbit_four (N : Nat) :
    orbitRepresentatives N 4 = orbitRepresentatives (orbitRepresentatives N 2) 2 := by
  unfold orbitRepresentatives
  rw [Nat.div_div_eq_div_mul]

/-- Transport of a discrete-log relation along a homomorphism of degree `d`. -/
theorem H087_transport (d x lg lq n n' : Nat) (hdiv : n' ∣ n)
    (h : lq % n = (x * lg) % n) : (d * lq) % n' = (x * (d * lg)) % n' := by
  have h1 : lq % n' = (x * lg) % n' := by
    rw [← Nat.mod_mod_of_dvd lq hdiv, h, Nat.mod_mod_of_dvd _ hdiv]
  rw [Nat.mul_mod, h1, ← Nat.mul_mod, Nat.mul_left_comm]

def H087_claim : Prop :=
  (∀ N, orbitRepresentatives N 6 = orbitRepresentatives (orbitRepresentatives N 2) 3) ∧
  ∀ (d x lg lq n n' : Nat), n' ∣ n → lq % n = (x * lg) % n →
    (d * lq) % n' = (x * (d * lg)) % n'

theorem H087_claim_holds : H087_claim := ⟨H087_orbit_six, H087_transport⟩

theorem H087_relation_ratio : orbitRepresentatives 600 6 * 3 = 300 := by decide

/-! ## H088 -/

/-- H088: Invariant-subspace dimension menu from x^n-1.
Handbook 10.2.1, 10.2.3, 15.1.3, 14.9.2, 5.4.3. ic_phase: curve-selection.
Claim: if 2 is primitive mod n, the cyclotomic cosets have sizes 1 and n-1, so stable
dimensions are only 0, 1, n-1, n (semisimplicity: stable subspaces = coset unions,
taken as a hypothesis). -/
def h088Ord (n : Nat) : Nat :=
  ((List.range n).find? (fun k => 2 ^ (k + 1) % n == 1)).elim 0 (· + 1)

def h088Dims : List Nat → List Nat
  | [] => [0]
  | s :: ss => h088Dims ss ++ (h088Dims ss).map (· + s)

def h088IsStable (S : List Bool → Prop) : Prop := ∀ v, S v → S (v.rotateLeft 1)

theorem H088_trivial_stable (n : Nat) :
    h088IsStable (fun v => v = List.replicate n false) ∧ h088IsStable (fun _ => True) := by
  refine ⟨?_, fun _ _ => trivial⟩
  intro v hv
  subst hv
  simp

theorem H088_zero_rot_11_13 :
    (List.replicate 11 false).rotateLeft 1 = List.replicate 11 false ∧
    (List.replicate 13 false).rotateLeft 1 = List.replicate 13 false := by decide

theorem H088_dims_primitive (n d : Nat) (hn : 1 ≤ n) (hd : d ∈ h088Dims [1, n - 1]) :
    d = 0 ∨ d = 1 ∨ d = n - 1 ∨ d = n := by
  simp [h088Dims] at hd
  omega

theorem H088_ord_values :
    h088Ord 11 = 10 ∧ h088Ord 13 = 12 ∧ h088Ord 73 = 9 ∧ h088Ord 89 = 11 ∧
    h088Ord 113 = 28 ∧ h088Ord 127 = 7 := by decide

def H088_claim : Prop :=
  ∀ (n : Nat) (StableDim : Nat → Prop) (sizes : List Nat),
    1 ≤ n → sizes = [1, n - 1] → (∀ d, StableDim d ↔ d ∈ h088Dims sizes) →
    ∀ d, StableDim d → d = 0 ∨ d = 1 ∨ d = n - 1 ∨ d = n

theorem H088_claim_holds : H088_claim := by
  intro n SD sizes hn hs hSD d hd
  subst hs
  exact H088_dims_primitive n d hn ((hSD d).mp hd)

/-! ## H089 -/

/-- H089: Berlekamp-Massey linear-complexity screen of Tr(x(kG)).
Handbook 10.4.2, 10.4.4.1. ic_phase: curve-selection.
Claim: a sequence with an order-r recurrence has linear complexity <= r and is determined
by its first r terms (soundness of BM with 2L terms); curve behaviour is a hypothesis. -/
def h089Step (c : List Bool) (s : Nat → Bool) (i : Nat) : Bool :=
  (List.range c.length).foldl (fun acc j => xor acc (c.getD j false && s (i + j))) false

def h089Rec (s : Nat → Bool) (c : List Bool) : Prop :=
  ∀ i, s (i + c.length) = h089Step c s i

def h089LCle (s : Nat → Bool) (r : Nat) : Prop :=
  ∃ c : List Bool, c.length ≤ r ∧ h089Rec s c

theorem H089_lc_mono (s : Nat → Bool) {r r' : Nat} (h : r ≤ r') (hs : h089LCle s r) :
    h089LCle s r' := by
  obtain ⟨c, hc, hr⟩ := hs
  exact ⟨c, Nat.le_trans hc h, hr⟩

theorem H089_fold_congr (c : List Bool) (s t : Nat → Bool) (i : Nat) (l : List Nat)
    (h : ∀ j ∈ l, s (i + j) = t (i + j)) (acc : Bool) :
    l.foldl (fun acc j => xor acc (c.getD j false && s (i + j))) acc
      = l.foldl (fun acc j => xor acc (c.getD j false && t (i + j))) acc := by
  induction l generalizing acc with
  | nil => rfl
  | cons j l ih =>
    simp only [List.foldl_cons]
    rw [h j List.mem_cons_self]
    exact ih (fun k hk => h k (List.mem_cons_of_mem j hk)) _

theorem H089_determined (c : List Bool) (s t : Nat → Bool)
    (hs : h089Rec s c) (ht : h089Rec t c)
    (h0 : ∀ i, i < c.length → s i = t i) : ∀ i, s i = t i := by
  intro i
  induction i using Nat.strongRecOn with
  | _ i ih =>
    by_cases hi : i < c.length
    · exact h0 i hi
    · obtain ⟨i0, rfl⟩ : ∃ i0, i = i0 + c.length := ⟨i - c.length, by omega⟩
      rw [hs i0, ht i0]
      unfold h089Step
      apply H089_fold_congr
      intro j hj
      have := List.mem_range.mp hj
      exact ih (i0 + j) (by omega)

theorem H089_bands :
    3 * 21 = 63 ∧ 2048 / 2 - 8 = 1016 ∧ 2048 / 2 + 8 = 1032 := by decide

def H089_claim : Prop :=
  ∀ (s t : Nat → Bool) (c : List Bool), h089Rec s c → h089Rec t c →
    (∀ i, i < c.length → s i = t i) → (∀ i, s i = t i)

theorem H089_claim_holds : H089_claim := fun s t c hs ht h0 => H089_determined c s t hs ht h0

/-! ## H090 -/

/-- H090: ONB canonical orbit key with trace as parity.
Handbook 16.7.4, 16.7.5. ic_phase: hardware.
Claim: the canonical rotation key is invariant under rotation and idempotent; a drop of the
canonicalisation phase with other phases unchanged is a genuine total improvement. -/
def h090Val (v : List Bool) : Nat := v.foldl (fun a b => 2 * a + if b then 1 else 0) 0

def h090Rots (v : List Bool) : List (List Bool) :=
  (List.range v.length).map (fun k => v.rotateLeft k)

def h090Canon (v : List Bool) : List Bool :=
  (h090Rots v).foldl (fun best w => if h090Val w < h090Val best then w else best) v

def h090All : Nat → List (List Bool)
  | 0 => [[]]
  | n + 1 => (h090All n).flatMap (fun v => [false :: v, true :: v])

def h090Check (n : Nat) : Bool :=
  (h090All n).all (fun v => (List.range n).all (fun j => h090Canon (v.rotateLeft j) == h090Canon v))

theorem H090_canon_idem (canon : List Bool → List Bool)
    (hinv : ∀ j v, canon (v.rotateLeft j) = canon v)
    (hrot : ∀ v, ∃ k, canon v = v.rotateLeft k) :
    ∀ v, canon (canon v) = canon v := by
  intro v
  obtain ⟨k, hk⟩ := hrot v
  calc canon (canon v) = canon (v.rotateLeft k) := by rw [← hk]
    _ = canon v := hinv k v

theorem H090_check_five : h090Check 5 = true := by decide

theorem H090_order_131 : 2 ^ 131 % 263 = 1 ∧ ∀ k, 0 < k → k < 131 → k ∣ 131 → 2 ^ k % 263 ≠ 1 := by
  refine ⟨by decide, ?_⟩
  intro k hk hk2 hd
  have : k = 1 := by
    have : ∀ k' : Fin 131, 0 < k'.val → k'.val ∣ 131 → k'.val = 1 := by decide
    exact this ⟨k, hk2⟩ hk hd
  subst this
  decide

theorem H090_cost_gain (c c' : Cost) (h : c.improvesRelations c') : c'.total < c.total :=
  Cost.total_lt_of_improvesRelations c c' h

def H090_claim : Prop :=
  ∀ (canon : List Bool → List Bool) (c c' : Cost),
    (∀ j v, canon (v.rotateLeft j) = canon v) →
    (∀ v, ∃ k, canon v = v.rotateLeft k) →
    c.improvesRelations c' →
    (∀ v, canon (canon v) = canon v) ∧ c'.beats c.total

theorem H090_claim_holds : H090_claim := by
  intro canon c c' hinv hrot hc
  exact ⟨H090_canon_idem canon hinv hrot, H090_cost_gain c c' hc⟩

end HandbookIC.Ideas.B09

#print axioms HandbookIC.Ideas.B09.b09_sum_const
#print axioms HandbookIC.Ideas.B09.H081_corr_identity
#print axioms HandbookIC.Ideas.B09.H081_dis_le
#print axioms HandbookIC.Ideas.B09.H081_corr_abs_le
#print axioms HandbookIC.Ideas.B09.b09_rotl_length
#print axioms HandbookIC.Ideas.B09.H081_C2_abs_le
#print axioms HandbookIC.Ideas.B09.H081_claim_holds
#print axioms HandbookIC.Ideas.B09.H082_prod_mono
#print axioms HandbookIC.Ideas.B09.H082_total_sum
#print axioms HandbookIC.Ideas.B09.H082_claim_holds
#print axioms HandbookIC.Ideas.B09.H083_sums_length
#print axioms HandbookIC.Ideas.B09.H083_coverage_step
#print axioms HandbookIC.Ideas.B09.H083_coverage_mono
#print axioms HandbookIC.Ideas.B09.H083_coverage_le
#print axioms HandbookIC.Ideas.B09.H083_claim_holds
#print axioms HandbookIC.Ideas.B09.b09_smooth_true
#print axioms HandbookIC.Ideas.B09.H084_partition
#print axioms HandbookIC.Ideas.B09.H084_amortised
#print axioms HandbookIC.Ideas.B09.H084_claim_holds
#print axioms HandbookIC.Ideas.B09.H085_choose_step
#print axioms HandbookIC.Ideas.B09.H085_choose_mono
#print axioms HandbookIC.Ideas.B09.H085_choose_small
#print axioms HandbookIC.Ideas.B09.H085_surj_card
#print axioms HandbookIC.Ideas.B09.H085_claim_holds
#print axioms HandbookIC.Ideas.B09.H086_orbit_closed
#print axioms HandbookIC.Ideas.B09.H086_countP_or
#print axioms HandbookIC.Ideas.B09.H086_countP_reps
#print axioms HandbookIC.Ideas.B09.H086_card_le
#print axioms HandbookIC.Ideas.B09.H086_claim_holds
#print axioms HandbookIC.Ideas.B09.H087_orbit_six
#print axioms HandbookIC.Ideas.B09.H087_orbit_four
#print axioms HandbookIC.Ideas.B09.H087_transport
#print axioms HandbookIC.Ideas.B09.H087_claim_holds
#print axioms HandbookIC.Ideas.B09.H087_relation_ratio
#print axioms HandbookIC.Ideas.B09.H088_trivial_stable
#print axioms HandbookIC.Ideas.B09.H088_zero_rot_11_13
#print axioms HandbookIC.Ideas.B09.H088_dims_primitive
#print axioms HandbookIC.Ideas.B09.H088_ord_values
#print axioms HandbookIC.Ideas.B09.H088_claim_holds
#print axioms HandbookIC.Ideas.B09.H089_lc_mono
#print axioms HandbookIC.Ideas.B09.H089_fold_congr
#print axioms HandbookIC.Ideas.B09.H089_determined
#print axioms HandbookIC.Ideas.B09.H089_bands
#print axioms HandbookIC.Ideas.B09.H089_claim_holds
#print axioms HandbookIC.Ideas.B09.H090_canon_idem
#print axioms HandbookIC.Ideas.B09.H090_check_five
#print axioms HandbookIC.Ideas.B09.H090_order_131
#print axioms HandbookIC.Ideas.B09.H090_cost_gain
#print axioms HandbookIC.Ideas.B09.H090_claim_holds
