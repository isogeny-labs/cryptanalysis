import HandbookIC.Core

namespace HandbookIC.Ideas.B02

open HandbookIC

/-! ## H011 -/

/-- H011: Primitive-polynomial LFSR enumeration of factor-base abscissae.
Handbook sections 11.1.1.3 (Primitive elements), 11.1.3.2 (Modular reduction
in extension fields). ic_phase: factor-base.
Claim: the factor base `{t^i}` for primitive `t` is enumerated with one shift
plus at most `hw(f)-1` XORs per element, at least 10x cheaper than random-x
sampling, with distinct entries for `B <= 2^n-1` and yield within 10%. -/
def h011Pow {G : Type} (mul : G → G → G) (one t : G) : Nat → G
  | 0 => one
  | k + 1 => mul t (h011Pow mul one t k)

/-- Bit-operation count of LFSR enumeration: one shift plus `hw - 1` XORs per element. -/
def h011EnumOps (B hw : Nat) : Nat := B * hw

theorem H011_pow_add {G : Type} (mul : G → G → G) (one t : G)
    (hassoc : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (hone : ∀ a, mul one a = a) (a b : Nat) :
    h011Pow mul one t (a + b) = mul (h011Pow mul one t a) (h011Pow mul one t b) := by
  induction a with
  | zero =>
    rw [Nat.zero_add, show h011Pow mul one t 0 = one from rfl, hone]
  | succ a ih =>
    have e : a + 1 + b = (a + b) + 1 := by omega
    rw [e]
    show mul t (h011Pow mul one t (a + b)) = mul (mul t (h011Pow mul one t a)) (h011Pow mul one t b)
    rw [ih, hassoc]

theorem H011_distinct_lt {G : Type} (mul : G → G → G) (one t : G) (N : Nat)
    (hassoc : ∀ a b c, mul (mul a b) c = mul a (mul b c))
    (hone : ∀ a, mul one a = a) (hmul_one : ∀ a, mul a one = a)
    (hcancel : ∀ a b c, mul a b = mul a c → b = c)
    (hord : ∀ k, 0 < k → k < N → h011Pow mul one t k ≠ one)
    (i j : Nat) (hij : i < j) (hjN : j < N)
    (h : h011Pow mul one t i = h011Pow mul one t j) : False := by
  obtain ⟨k, rfl⟩ := Nat.exists_eq_add_of_lt hij
  have e : i + k + 1 = i + (k + 1) := by omega
  rw [e] at h
  have hk := H011_pow_add mul one t hassoc hone i (k + 1)
  have h1 : mul (h011Pow mul one t i) (h011Pow mul one t (k + 1))
      = mul (h011Pow mul one t i) one := by
    rw [← hk, ← h, hmul_one]
  have h2 := hcancel _ _ _ h1
  exact hord (k + 1) (by omega) (by omega) h2

def H011_claim : Prop :=
  ∀ (G : Type) (mul : G → G → G) (one t : G) (N : Nat),
    (∀ a b c, mul (mul a b) c = mul a (mul b c)) →
    (∀ a, mul one a = a) → (∀ a, mul a one = a) →
    (∀ a b c, mul a b = mul a c → b = c) →
    (∀ k, 0 < k → k < N → h011Pow mul one t k ≠ one) →
    ∀ B, B ≤ N → ∀ i j, i < B → j < B →
      h011Pow mul one t i = h011Pow mul one t j → i = j

theorem H011_distinct : H011_claim := by
  intro G mul one t N hassoc hone hmul_one hcancel hord B hB i j hi hj h
  rcases Nat.lt_trichotomy i j with hlt | heq | hgt
  · exact (H011_distinct_lt mul one t N hassoc hone hmul_one hcancel hord i j hlt
      (by omega) h).elim
  · exact heq
  · exact (H011_distinct_lt mul one t N hassoc hone hmul_one hcancel hord j i hgt
      (by omega) h.symm).elim

/-- If one LFSR step (hw ops) is at least 10x cheaper than one random-x sample
(cost `s`), the whole enumeration is at least 10x cheaper. -/
theorem H011_enum_cost_ratio (B hw s : Nat) (h : hw * 10 ≤ s) :
    h011EnumOps B hw * 10 ≤ B * s := by
  unfold h011EnumOps
  rw [Nat.mul_assoc]
  exact Nat.mul_le_mul_left B h

/-! ## H012 -/

/-- H012: Factor base restricted to the cofactor image subgroup via a character test.
Handbook sections 10.1.4.3 (Characteristic functions), 10.1.4.4 (Gauss sums).
ic_phase: factor-base.
Claim: drawing `F` only from a subgroup `H` of size `N/h` (closed under add,
`F ⊆ H`) makes pair-sum fibres average at least `B^2/|H| = h B^2/N`, so some
sum value is hit at least that often. -/
def h012Cnt (k : Nat) : List Nat → Nat
  | [] => 0
  | x :: xs => (if x = k then 1 else 0) + h012Cnt k xs

def h012Rm (k : Nat) : List Nat → List Nat
  | [] => []
  | x :: xs => if x = k then h012Rm k xs else x :: h012Rm k xs

theorem h012_len_split (k : Nat) (xs : List Nat) :
    xs.length = h012Cnt k xs + (h012Rm k xs).length := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    by_cases h : x = k
    · simp only [h012Cnt, h012Rm, if_pos h, List.length_cons]; omega
    · simp only [h012Cnt, h012Rm, if_neg h, List.length_cons]; omega

theorem h012_cnt_rm_ne (j k : Nat) (hjk : j ≠ k) (xs : List Nat) :
    h012Cnt j (h012Rm k xs) = h012Cnt j xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    by_cases h : x = k
    · have hx : ¬ (x = j) := fun e => hjk (e.symm.trans h)
      simp only [h012Cnt, h012Rm, if_pos h, if_neg hx]
      omega
    · by_cases hj : x = j
      · simp only [h012Cnt, h012Rm, if_neg h, if_pos hj]
        omega
      · simp only [h012Cnt, h012Rm, if_neg h, if_neg hj]
        omega

theorem h012_rm_lt (k : Nat) (xs : List Nat) (h : ∀ y ∈ xs, y < k + 1) :
    ∀ y ∈ h012Rm k xs, y < k := by
  induction xs with
  | nil => intro y hy; simp [h012Rm] at hy
  | cons x xs ih =>
    intro y hy
    by_cases hx : x = k
    · simp only [h012Rm, if_pos hx] at hy
      exact ih (fun z hz => h z (List.mem_cons_of_mem _ hz)) y hy
    · simp only [h012Rm, if_neg hx] at hy
      rcases List.mem_cons.mp hy with e | e
      · have := h x (List.mem_cons_self ..)
        omega
      · exact ih (fun z hz => h z (List.mem_cons_of_mem _ hz)) y e

theorem h012_pigeon (M : Nat) : ∀ xs : List Nat, (∀ x ∈ xs, x < M + 1) →
    ∃ k, k ≤ M ∧ xs.length ≤ (M + 1) * h012Cnt k xs := by
  induction M with
  | zero =>
    intro xs h
    refine ⟨0, Nat.le_refl _, ?_⟩
    have hr : (h012Rm 0 xs).length = 0 := by
      cases hh : h012Rm 0 xs with
      | nil => rfl
      | cons y ys =>
        have := h012_rm_lt 0 xs h y (by rw [hh]; exact List.mem_cons_self ..)
        omega
    have := h012_len_split 0 xs
    omega
  | succ M ih =>
    intro xs h
    have hr : ∀ y ∈ h012Rm (M + 1) xs, y < M + 1 := h012_rm_lt (M + 1) xs h
    obtain ⟨k, hk, hle⟩ := ih (h012Rm (M + 1) xs) hr
    have hsplit := h012_len_split (M + 1) xs
    have hne : k ≠ M + 1 := by omega
    have hc := h012_cnt_rm_ne k (M + 1) hne xs
    rw [hc] at hle
    by_cases hcmp : h012Cnt (M + 1) xs ≤ h012Cnt k xs
    · refine ⟨k, by omega, ?_⟩
      have e : (M + 1 + 1) * h012Cnt k xs = (M + 1) * h012Cnt k xs + h012Cnt k xs := by
        rw [Nat.add_mul, Nat.one_mul]
      omega
    · refine ⟨M + 1, Nat.le_refl _, ?_⟩
      have h3 : (M + 1) * h012Cnt k xs ≤ (M + 1) * h012Cnt (M + 1) xs :=
        Nat.mul_le_mul_left _ (by omega)
      have e : (M + 1 + 1) * h012Cnt (M + 1) xs
          = (M + 1) * h012Cnt (M + 1) xs + h012Cnt (M + 1) xs := by
        rw [Nat.add_mul, Nat.one_mul]
      omega

def H012_claim : Prop :=
  ∀ (B M : Nat) (sums : List Nat), 0 < M → sums.length = B * B →
    (∀ s ∈ sums, s < M) → ∃ k, k < M ∧ B * B ≤ M * h012Cnt k sums

theorem H012_pair_fibre_average : H012_claim := by
  intro B M sums hM hlen hlt
  cases M with
  | zero => omega
  | succ M' =>
    obtain ⟨k, hk, hle⟩ := h012_pigeon M' sums hlt
    exact ⟨k, by omega, by rw [← hlen]; exact hle⟩

/-- Closure of a subgroup predicate: pair sums of factor-base entries stay in `H`. -/
theorem H012_pair_sum_mem {G : Type} {B : Nat} (add : G → G → G) (H : G → Prop)
    (hc : ∀ a b, H a → H b → H (add a b)) (F : FactorBase G B)
    (hF : ∀ i, H (F i)) (i j : Fin B) : H (add (F i) (F j)) :=
  hc _ _ (hF i) (hF j)

/-! ## H013 -/

/-- H013: Valid-point fraction of Frobenius-invariant subspaces (orbit-level variance).
Handbook sections 9.1.2 (Walsh transform), 9.1.1.2 (Trace representation).
ic_phase: factor-base.
Claim: when the point-existence indicator is orbit-constant, `validCount` is the
sum over orbit representatives of orbit size times the indicator, and
relations are bounded by `validCount^m`. -/
structure h013Orbit where
  rep : Nat
  rest : List Nat

def h013Elems (orbs : List h013Orbit) : List Nat :=
  orbs.flatMap (fun o => o.rep :: o.rest)

def h013Valid (isPoint : Nat → Bool) (orbs : List h013Orbit) : Nat :=
  smoothCount (h013Elems orbs) isPoint

def h013RepSum (isPoint : Nat → Bool) : List h013Orbit → Nat
  | [] => 0
  | o :: os => (if isPoint o.rep then o.rest.length + 1 else 0) + h013RepSum isPoint os

theorem h013_filter_const (p : Nat → Bool) (b : Bool) (rest : List Nat)
    (h : ∀ y ∈ rest, p y = b) :
    (rest.filter p).length = if b then rest.length else 0 := by
  induction rest with
  | nil => simp
  | cons y ys ih =>
    have hy := h y (List.mem_cons_self ..)
    have ih' := ih (fun z hz => h z (List.mem_cons_of_mem _ hz))
    cases b
    · simp [List.filter_cons, hy] at ih' ⊢
      exact ih'
    · simp [List.filter_cons, hy] at ih' ⊢
      exact ih'

def H013_claim : Prop :=
  ∀ (isPoint : Nat → Bool) (orbs : List h013Orbit) (m rel : Nat),
    (∀ o ∈ orbs, ∀ y ∈ o.rest, isPoint y = isPoint o.rep) →
    h013Valid isPoint orbs = h013RepSum isPoint orbs ∧
    (rel ≤ (h013Valid isPoint orbs) ^ m → rel ≤ (h013RepSum isPoint orbs) ^ m)

theorem H013_valid_eq_repsum (isPoint : Nat → Bool) (orbs : List h013Orbit)
    (h : ∀ o ∈ orbs, ∀ y ∈ o.rest, isPoint y = isPoint o.rep) :
    h013Valid isPoint orbs = h013RepSum isPoint orbs := by
  unfold h013Valid smoothCount
  induction orbs with
  | nil => simp [h013Elems, h013RepSum]
  | cons o os ih =>
    have ih' := ih (fun o' ho' => h o' (List.mem_cons_of_mem _ ho'))
    have ho := h o (List.mem_cons_self ..)
    have key := h013_filter_const isPoint (isPoint o.rep) o.rest ho
    have e : h013Elems (o :: os) = (o.rep :: o.rest) ++ h013Elems os := by
      simp [h013Elems, List.flatMap_cons]
    rw [e, List.filter_append, List.length_append, h013RepSum]
    rw [ih']
    cases hp : isPoint o.rep
    · simp [List.filter_cons, hp] at key ⊢
      omega
    · simp [List.filter_cons, hp] at key ⊢
      omega

theorem H013_claim_holds : H013_claim := by
  intro isPoint orbs m rel h
  have e := H013_valid_eq_repsum isPoint orbs h
  exact ⟨e, by rw [← e]; exact id⟩

theorem H013_valid_le_total (isPoint : Nat → Bool) (orbs : List h013Orbit) :
    h013Valid isPoint orbs ≤ (h013Elems orbs).length :=
  smoothCount_le_length _ _

/-! ## H014 -/

/-- H014: Swap hill-climbing on exact S3 yield N(V).
Handbook sections 9.1.3 (Parameters of Boolean functions), 9.1.1.1 (ANF).
ic_phase: factor-base.
Claim: if `g` is additive (xor) with kernel `{0, e}`, then for fixed `(x1,x2)`
the `x3`-solutions of `g x3 = c x1 x2` in a duplicate-free `V` number at most 2,
so the total solution count is at most `2 |V|^2`. -/
def h014Sols (g : Nat → Nat) (c : Nat → Nat → Nat) (V : List Nat) : List Nat :=
  V.flatMap fun x1 => V.flatMap fun x2 => V.filter (fun x3 => g x3 == c x1 x2)

theorem h014_two_bound (a b : Nat) (l : List Nat) (hnd : l.Nodup)
    (h : ∀ y ∈ l, y = a ∨ y = b) : l.length ≤ 2 := by
  match l, hnd, h with
  | [], _, _ => simp
  | [_], _, _ => simp
  | [_, _], _, _ => simp
  | x :: y :: z :: zs, hnd, h =>
    exfalso
    have hx := h x (by simp)
    have hy := h y (by simp)
    have hz := h z (by simp)
    simp only [List.nodup_cons, List.mem_cons, not_or] at hnd
    obtain ⟨⟨hxy, hxz, _⟩, ⟨hyz, _⟩, _⟩ := hnd
    omega

theorem h014_flat_len {α β : Type} (f : α → List β) (k : Nat) :
    ∀ L : List α, (∀ a ∈ L, (f a).length ≤ k) → (L.flatMap f).length ≤ k * L.length := by
  intro L
  induction L with
  | nil => intro _; simp
  | cons a as ih =>
    intro h
    have h1 := h a (List.mem_cons_self ..)
    have h2 := ih (fun x hx => h x (List.mem_cons_of_mem _ hx))
    have e : k * (as.length + 1) = k * as.length + k := Nat.mul_succ _ _
    simp only [List.flatMap_cons, List.length_append, List.length_cons]
    omega

theorem H014_fibre_le_two (g : Nat → Nat) (e : Nat)
    (hadd : ∀ a b, g (a ^^^ b) = g a ^^^ g b)
    (hker : ∀ z, g z = 0 → z = 0 ∨ z = e)
    (V : List Nat) (hV : V.Nodup) (c0 : Nat) :
    (V.filter (fun x => g x == c0)).length ≤ 2 := by
  have hnd := hV.filter (fun x => g x == c0)
  cases hl : V.filter (fun x => g x == c0) with
  | nil => simp
  | cons a rest =>
    rw [hl] at hnd
    apply h014_two_bound a (e ^^^ a) _ hnd
    intro y hy
    have hya : y ∈ V.filter (fun x => g x == c0) := by rw [hl]; exact hy
    have ha : a ∈ V.filter (fun x => g x == c0) := by rw [hl]; exact List.mem_cons_self ..
    simp only [List.mem_filter, beq_iff_eq] at hya ha
    have hz : g (y ^^^ a) = 0 := by rw [hadd, hya.2, ha.2, Nat.xor_self]
    have hy' : y = (y ^^^ a) ^^^ a := by rw [Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]
    rcases hker _ hz with h0 | he
    · left; rw [h0, Nat.zero_xor] at hy'; exact hy'
    · right; rw [he] at hy'; exact hy'

def H014_claim : Prop :=
  ∀ (g : Nat → Nat) (e : Nat) (c : Nat → Nat → Nat) (V : List Nat),
    (∀ a b, g (a ^^^ b) = g a ^^^ g b) →
    (∀ z, g z = 0 → z = 0 ∨ z = e) → V.Nodup →
    (h014Sols g c V).length ≤ 2 * (V.length * V.length)

theorem H014_total_le : H014_claim := by
  intro g e c V hadd hker hV
  unfold h014Sols
  have inner : ∀ x1 ∈ V, (V.flatMap fun x2 => V.filter (fun x3 => g x3 == c x1 x2)).length
      ≤ 2 * V.length := fun x1 _ =>
    h014_flat_len _ 2 V (fun x2 _ => H014_fibre_le_two g e hadd hker V hV _)
  have := h014_flat_len _ (2 * V.length) V inner
  rw [Nat.mul_assoc] at this
  exact this

/-! ## H015 -/

/-- H015: Best-of-T scaling/translate of V by Kloosterman liftable bias.
Handbook sections 7.1.4 (Artin-Schreier hypersurfaces), 6.3.5 (Incomplete
character sums). ic_phase: factor-base.
Claim: the best of `T` candidate subspaces has liftCount at least the average,
and the relation-collection cost `N / c^m` is antitone in the yield ratio `c`
(Nat.div_le_div_left), so the best-of-T never costs more. -/
def h015Max : List Nat → Nat
  | [] => 0
  | x :: xs => max x (h015Max xs)

def h015Sum : List Nat → Nat
  | [] => 0
  | x :: xs => x + h015Sum xs

def h015Rel (N c m : Nat) : Nat := N / c ^ m

def h015Cost (base : Cost) (N c m : Nat) : Cost :=
  { base with relations := h015Rel N c m }

theorem h015_le_max (xs : List Nat) : ∀ x ∈ xs, x ≤ h015Max xs := by
  induction xs with
  | nil => intro x hx; simp at hx
  | cons y ys ih =>
    intro x hx
    simp only [h015Max]
    rcases List.mem_cons.mp hx with e | e
    · subst e; exact Nat.le_max_left _ _
    · exact Nat.le_trans (ih x e) (Nat.le_max_right _ _)

theorem H015_sum_le_len_mul_max (xs : List Nat) :
    h015Sum xs ≤ xs.length * h015Max xs := by
  induction xs with
  | nil => simp [h015Sum]
  | cons x xs ih =>
    have h1 : h015Max xs ≤ h015Max (x :: xs) := Nat.le_max_right _ _
    have h2 : x ≤ h015Max (x :: xs) := Nat.le_max_left _ _
    have h3 : xs.length * h015Max xs ≤ xs.length * h015Max (x :: xs) :=
      Nat.mul_le_mul_left _ h1
    have e : (xs.length + 1) * h015Max (x :: xs)
        = xs.length * h015Max (x :: xs) + h015Max (x :: xs) := by
      rw [Nat.add_mul, Nat.one_mul]
    simp only [h015Sum, List.length_cons]
    omega

theorem H015_rel_antitone (N m c c' : Nat) (hc : 0 < c) (hcc : c ≤ c') :
    h015Rel N c' m ≤ h015Rel N c m := by
  unfold h015Rel
  exact Nat.div_le_div_left (Nat.pow_le_pow_left hcc m) (Nat.pow_pos hc)

theorem H015_cost_improves (base : Cost) (N m c c' : Nat) (hc : 0 < c) (hcc : c ≤ c')
    (hstrict : h015Rel N c' m < h015Rel N c m) :
    (h015Cost base N c m).improvesRelations (h015Cost base N c' m) ∧
    (h015Cost base N c' m).total < (h015Cost base N c m).total := by
  have hi : (h015Cost base N c m).improvesRelations (h015Cost base N c' m) :=
    ⟨rfl, rfl, rfl, hstrict⟩
  exact ⟨hi, Cost.total_lt_of_improvesRelations _ _ hi⟩

def H015_claim : Prop :=
  ∀ (counts : List Nat) (N m c c' : Nat),
    h015Sum counts ≤ counts.length * h015Max counts ∧
    (0 < c → c ≤ c' → h015Rel N c' m ≤ h015Rel N c m)

theorem H015_claim_holds : H015_claim := fun counts N m c c' =>
  ⟨H015_sum_le_len_mul_max counts, fun hc hcc => H015_rel_antitone N m c c' hc hcc⟩

/-! ## H016 -/

/-- H016: Affine-hull dimension of S3(V^3) as subspace selection criterion.
Handbook section 6.4.2 (Sum-product estimate). ic_phase: factor-base.
Claim: with hull dimension `w <= n`, the expected relation count
`N * 2^(n-w) / |V|^2` is antitone in `w` and equals the generic count at `w = n`. -/
def h016Rel (N n v w : Nat) : Nat := N * 2 ^ (n - w) / (v * v)

theorem H016_antitone (N n v w w' : Nat) (hw : w ≤ w') (hn : w' ≤ n) :
    h016Rel N n v w' ≤ h016Rel N n v w := by
  unfold h016Rel
  apply Nat.div_le_div_right
  apply Nat.mul_le_mul_left
  exact Nat.pow_le_pow_right (by decide) (by omega)

theorem H016_generic_at_full (N n v : Nat) : h016Rel N n v n = N / (v * v) := by
  unfold h016Rel
  simp

theorem H016_hull_at_least_generic (N n v w : Nat) (hn : w ≤ n) :
    N / (v * v) ≤ h016Rel N n v w := by
  rw [← H016_generic_at_full N n v]
  exact H016_antitone N n v w n hn (Nat.le_refl _)

def H016_claim : Prop :=
  ∀ (N n v w w' : Nat), w ≤ w' → w' ≤ n →
    h016Rel N n v w' ≤ h016Rel N n v w ∧ h016Rel N n v n = N / (v * v)

theorem H016_claim_holds : H016_claim := fun N n v w w' h1 h2 =>
  ⟨H016_antitone N n v w w' h1 h2, H016_generic_at_full N n v⟩

/-! ## H017 -/

/-- H017: Legendre-biased multiplicative coset selection for prime-field factor bases.
Handbook sections 7.1.5 (Kummer hypersurfaces), 7.3.2 (Jacobi sums).
ic_phase: factor-base.
Claim: `x3` is in `F_p` iff `chi(f(x1)) = chi(f(x2))`; with `a` plus-signs and
`b` minus-signs among `B = a+b` base elements the number of agreeing ordered
pairs is `a^2+b^2 >= B^2/2`, and the relation cost `N/c^3` is antitone in the
lift ratio `c`; the best coset has liftCount at least the average. -/
def h017Agree (a b : Nat) : Nat := a * a + b * b

def h017Cost (base : Cost) (N c : Nat) : Cost :=
  { base with relations := N / c ^ 3 }

theorem H017_agree_ge_half (a b : Nat) : (a + b) * (a + b) ≤ 2 * h017Agree a b := by
  unfold h017Agree
  rcases Nat.le_total a b with h | h
  · obtain ⟨d, rfl⟩ := Nat.exists_eq_add_of_le h
    simp only [Nat.mul_add, Nat.add_mul]
    omega
  · obtain ⟨d, rfl⟩ := Nat.exists_eq_add_of_le h
    simp only [Nat.mul_add, Nat.add_mul]
    omega

theorem H017_cost_antitone (N c c' : Nat) (hc : 0 < c) (hcc : c ≤ c') :
    (h017Cost { factorBase := 0, relations := 0, linearAlgebra := 0, descent := 0 } N c').relations
    ≤ (h017Cost { factorBase := 0, relations := 0, linearAlgebra := 0, descent := 0 } N c).relations := by
  unfold h017Cost
  exact Nat.div_le_div_left (Nat.pow_le_pow_left hcc 3) (Nat.pow_pos hc)

def H017_claim : Prop :=
  ∀ (a b N c c' : Nat) (counts : List Nat),
    (a + b) * (a + b) ≤ 2 * h017Agree a b ∧
    h015Sum counts ≤ counts.length * h015Max counts ∧
    (0 < c → c ≤ c' → N / c' ^ 3 ≤ N / c ^ 3)

theorem H017_claim_holds : H017_claim := by
  intro a b N c c' counts
  refine ⟨H017_agree_ge_half a b, H015_sum_le_len_mul_max counts, ?_⟩
  intro hc hcc
  exact Nat.div_le_div_left (Nat.pow_le_pow_left hcc 3) (Nat.pow_pos hc)

/-! ## H018 -/

/-- H018: Rotation-closed Hamming-ball necklace factor base for primitive-root n.
Handbook sections 5.2.1 (Normal bases), 5.3.1 (Low complexity normal bases),
14.9.2 (Weights of multiples). ic_phase: factor-base.
Claim: with `rot` the cyclic shift (Frobenius in an ONB), Hamming weight is
rot-invariant, so `{wt <= w}` is rot-closed, and a vector fixed by `rot` is
constant (weight 0 or full length). -/
def h018Rot : List Bool → List Bool
  | [] => []
  | x :: xs => xs ++ [x]

def h018Wt : List Bool → Nat
  | [] => 0
  | b :: bs => (if b then 1 else 0) + h018Wt bs

def h018Ball (w : Nat) (v : List Bool) : Prop := h018Wt v ≤ w

theorem h018_wt_append (xs ys : List Bool) : h018Wt (xs ++ ys) = h018Wt xs + h018Wt ys := by
  induction xs with
  | nil => simp [h018Wt]
  | cons x xs ih => simp only [List.cons_append, h018Wt, ih]; omega

theorem H018_wt_rot (v : List Bool) : h018Wt (h018Rot v) = h018Wt v := by
  cases v with
  | nil => rfl
  | cons x xs =>
    simp only [h018Rot, h018_wt_append, h018Wt]
    omega

theorem H018_ball_closed (w : Nat) (v : List Bool) (h : h018Ball w v) :
    h018Ball w (h018Rot v) := by
  unfold h018Ball at *
  rw [H018_wt_rot]; exact h

theorem h018_fixed_const (x : Bool) (xs : List Bool) (h : xs ++ [x] = x :: xs) :
    ∀ z ∈ xs, z = x := by
  induction xs with
  | nil => intro z hz; simp at hz
  | cons y ys ih =>
    simp only [List.cons_append, List.cons.injEq] at h
    obtain ⟨hy, hys⟩ := h
    subst hy
    intro z hz
    rcases List.mem_cons.mp hz with e | e
    · exact e
    · exact ih hys z e

theorem h018_wt_const (x : Bool) (xs : List Bool) (h : ∀ z ∈ xs, z = x) :
    h018Wt xs = if x then xs.length else 0 := by
  induction xs with
  | nil => cases x <;> simp [h018Wt]
  | cons y ys ih =>
    have hy := h y (List.mem_cons_self ..)
    have ih' := ih (fun z hz => h z (List.mem_cons_of_mem _ hz))
    subst hy
    cases y <;> simp [h018Wt] at ih' ⊢ <;> omega

theorem H018_fixed_weight (v : List Bool) (h : h018Rot v = v) :
    h018Wt v = 0 ∨ h018Wt v = v.length := by
  cases v with
  | nil => left; rfl
  | cons x xs =>
    simp only [h018Rot] at h
    have hc := h018_fixed_const x xs h
    have hw := h018_wt_const x xs hc
    cases x
    · left; simp [h018Wt, hw]
    · right; simp [h018Wt, hw]; omega

def H018_claim : Prop :=
  ∀ (w : Nat) (v : List Bool),
    h018Wt (h018Rot v) = h018Wt v ∧ (h018Ball w v → h018Ball w (h018Rot v)) ∧
    (h018Rot v = v → h018Wt v = 0 ∨ h018Wt v = v.length)

theorem H018_claim_holds : H018_claim := fun w v =>
  ⟨H018_wt_rot v, H018_ball_closed w v, H018_fixed_weight v⟩

/-! ## H019 -/

/-- H019: Groebner-fan bi-weight order for the bilinear S3 subspace system.
Handbook section 17.1.4.2 (Groebner fan parameter estimation).
ic_phase: decomposition.
Claim: for a system bilinear (xor-additive in each argument) the solution set
for fixed `b` is closed under xor-differences into the kernel
(`F (a ^ a') b = 0`), `F 0 b = 0 = F a 0`, and the solution count decomposes as a
sum of per-`a` fibre counts (toy instance checked by `decide`). -/
structure h019Sys where
  F : Nat → Nat → Nat
  bilinear_a : ∀ a a' b, F (a ^^^ a') b = F a b ^^^ F a' b
  bilinear_b : ∀ a b b', F a (b ^^^ b') = F a b ^^^ F a b'

def h019Sols (F : Nat → Nat → Nat) (c : Nat) (V W : List Nat) : List (Nat × Nat) :=
  V.flatMap (fun a => (W.filter (fun b => F a b == c)).map (fun b => (a, b)))

def h019Sum : List Nat → Nat
  | [] => 0
  | x :: xs => x + h019Sum xs

theorem H019_zero_left (S : h019Sys) (b : Nat) : S.F 0 b = 0 := by
  have h := S.bilinear_a 0 0 b
  rw [Nat.xor_self] at h
  have h2 : S.F 0 b ^^^ S.F 0 b = 0 := Nat.xor_self _
  rw [← h] at h2
  -- h : F 0 b = F 0 b ^^^ F 0 b
  rw [h]; exact Nat.xor_self _

theorem H019_kernel (S : h019Sys) (a a' b c : Nat)
    (h1 : S.F a b = c) (h2 : S.F a' b = c) : S.F (a ^^^ a') b = 0 := by
  rw [S.bilinear_a, h1, h2, Nat.xor_self]

theorem H019_len_decomp (F : Nat → Nat → Nat) (c : Nat) (W : List Nat) :
    ∀ V : List Nat, (h019Sols F c V W).length
      = h019Sum (V.map fun a => (W.filter (fun b => F a b == c)).length) := by
  intro V
  induction V with
  | nil => simp [h019Sols, h019Sum]
  | cons a as ih =>
    unfold h019Sols at *
    simp only [List.flatMap_cons, List.length_append, List.length_map, List.map_cons,
      h019Sum, ih]

def H019_claim : Prop :=
  ∀ (S : h019Sys) (c : Nat) (V W : List Nat),
    (∀ b, S.F 0 b = 0) ∧
    (∀ a a' b, S.F a b = c → S.F a' b = c → S.F (a ^^^ a') b = 0) ∧
    (h019Sols S.F c V W).length
      = h019Sum (V.map fun a => (W.filter (fun b => S.F a b == c)).length)

theorem H019_claim_holds : H019_claim := fun S c V W =>
  ⟨H019_zero_left S, fun a a' b h1 h2 => H019_kernel S a a' b c h1 h2,
   H019_len_decomp S.F c W V⟩

/-- Toy instance: `F a b = a &&& b` on `0..3`, zero set has 9 pairs. -/
theorem H019_toy_count :
    (h019Sols (fun a b => a &&& b) 0 (List.range 4) (List.range 4)).length = 9 := by
  decide

/-! ## H020 -/

/-- H020: Canalyzing-depth pre-sieve for the post-trace decomposition predicate.
Handbook sections 17.1.4.1 (Minimal-sets algorithm), 17.1.6.1 (Nested
canalyzing functions). ic_phase: decomposition.
Claim (negative route): a predicate on `m` bits with no canalyzing variable has
no one-bit pre-sieve; pre-sieves derived from a determining set are sound
(discard only inputs with the known output), and determining sets are monotone
in the variable set. -/
def h020Canal (f : Nat → Bool) (m i : Nat) (a b : Bool) : Prop :=
  ∀ x, x < 2 ^ m → x.testBit i = a → f x = b

def h020DetSet (f : Nat → Bool) (m : Nat) (S : List Nat) (vals : Nat → Bool) (b : Bool) : Prop :=
  ∀ x, x < 2 ^ m → (∀ i ∈ S, x.testBit i = vals i) → f x = b

def h020Match (S : List Nat) (vals : Nat → Bool) (x : Nat) : Prop :=
  ∀ i ∈ S, x.testBit i = vals i

theorem H020_presieve_sound (f : Nat → Bool) (m : Nat) (S : List Nat) (vals : Nat → Bool)
    (h : h020DetSet f m S vals false) (x : Nat) (hx : x < 2 ^ m) (hf : f x = true) :
    ¬ h020Match S vals x := by
  intro hm
  have := h x hx hm
  rw [hf] at this
  exact Bool.noConfusion this

theorem H020_detset_mono (f : Nat → Bool) (m : Nat) (S S' : List Nat) (vals : Nat → Bool)
    (b : Bool) (hsub : ∀ i ∈ S, i ∈ S') (h : h020DetSet f m S vals b) :
    h020DetSet f m S' vals b := by
  intro x hx hm
  exact h x hx (fun i hi => hm i (hsub i hi))

theorem H020_canal_is_detset (f : Nat → Bool) (m i : Nat) (a b : Bool)
    (h : h020Canal f m i a b) : h020DetSet f m [i] (fun _ => a) b := by
  intro x hx hm
  exact h x hx (hm i (List.mem_cons_self ..))

/-- 3-bit parity has no canalyzing variable, so no one-bit pre-sieve exists. -/
theorem H020_parity3_no_canal :
    ∀ i, i < 3 → ∀ a b : Bool,
      ¬ h020Canal (fun x => x.testBit 0 ^^ x.testBit 1 ^^ x.testBit 2) 3 i a b := by
  unfold h020Canal
  decide

/-- 3-bit AND does have a canalyzing variable (bit 0 = false forces output false). -/
theorem H020_and3_canal :
    h020Canal (fun x => x.testBit 0 && x.testBit 1 && x.testBit 2) 3 0 false false := by
  unfold h020Canal
  decide

def H020_claim : Prop :=
  ∀ (f : Nat → Bool) (m : Nat) (S S' : List Nat) (vals : Nat → Bool),
    (∀ i ∈ S, i ∈ S') →
    h020DetSet f m S vals false →
    h020DetSet f m S' vals false ∧
    (∀ x, x < 2 ^ m → f x = true → ¬ h020Match S vals x)

theorem H020_claim_holds : H020_claim := by
  intro f m S S' vals hsub h
  exact ⟨H020_detset_mono f m S S' vals false hsub h,
    fun x hx hf => H020_presieve_sound f m S vals h x hx hf⟩

end HandbookIC.Ideas.B02

#print axioms HandbookIC.Ideas.B02.H011_pow_add
#print axioms HandbookIC.Ideas.B02.H011_distinct_lt
#print axioms HandbookIC.Ideas.B02.H011_distinct
#print axioms HandbookIC.Ideas.B02.H011_enum_cost_ratio
#print axioms HandbookIC.Ideas.B02.h012_len_split
#print axioms HandbookIC.Ideas.B02.h012_cnt_rm_ne
#print axioms HandbookIC.Ideas.B02.h012_rm_lt
#print axioms HandbookIC.Ideas.B02.h012_pigeon
#print axioms HandbookIC.Ideas.B02.H012_pair_fibre_average
#print axioms HandbookIC.Ideas.B02.H012_pair_sum_mem
#print axioms HandbookIC.Ideas.B02.h013_filter_const
#print axioms HandbookIC.Ideas.B02.H013_valid_eq_repsum
#print axioms HandbookIC.Ideas.B02.H013_claim_holds
#print axioms HandbookIC.Ideas.B02.H013_valid_le_total
#print axioms HandbookIC.Ideas.B02.h014_two_bound
#print axioms HandbookIC.Ideas.B02.h014_flat_len
#print axioms HandbookIC.Ideas.B02.H014_fibre_le_two
#print axioms HandbookIC.Ideas.B02.H014_total_le
#print axioms HandbookIC.Ideas.B02.h015_le_max
#print axioms HandbookIC.Ideas.B02.H015_sum_le_len_mul_max
#print axioms HandbookIC.Ideas.B02.H015_rel_antitone
#print axioms HandbookIC.Ideas.B02.H015_cost_improves
#print axioms HandbookIC.Ideas.B02.H015_claim_holds
#print axioms HandbookIC.Ideas.B02.H016_antitone
#print axioms HandbookIC.Ideas.B02.H016_generic_at_full
#print axioms HandbookIC.Ideas.B02.H016_hull_at_least_generic
#print axioms HandbookIC.Ideas.B02.H016_claim_holds
#print axioms HandbookIC.Ideas.B02.H017_agree_ge_half
#print axioms HandbookIC.Ideas.B02.H017_cost_antitone
#print axioms HandbookIC.Ideas.B02.H017_claim_holds
#print axioms HandbookIC.Ideas.B02.h018_wt_append
#print axioms HandbookIC.Ideas.B02.H018_wt_rot
#print axioms HandbookIC.Ideas.B02.H018_ball_closed
#print axioms HandbookIC.Ideas.B02.h018_fixed_const
#print axioms HandbookIC.Ideas.B02.h018_wt_const
#print axioms HandbookIC.Ideas.B02.H018_fixed_weight
#print axioms HandbookIC.Ideas.B02.H018_claim_holds
#print axioms HandbookIC.Ideas.B02.H019_zero_left
#print axioms HandbookIC.Ideas.B02.H019_kernel
#print axioms HandbookIC.Ideas.B02.H019_len_decomp
#print axioms HandbookIC.Ideas.B02.H019_claim_holds
#print axioms HandbookIC.Ideas.B02.H019_toy_count
#print axioms HandbookIC.Ideas.B02.H020_presieve_sound
#print axioms HandbookIC.Ideas.B02.H020_detset_mono
#print axioms HandbookIC.Ideas.B02.H020_canal_is_detset
#print axioms HandbookIC.Ideas.B02.H020_parity3_no_canal
#print axioms HandbookIC.Ideas.B02.H020_and3_canal
#print axioms HandbookIC.Ideas.B02.H020_claim_holds
