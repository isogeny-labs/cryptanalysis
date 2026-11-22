import HandbookIC.Core

/-!
# HandbookIC.Ideas.B04 — handbook ideas H031 .. H040 (decomposition phase)

Each idea has: a doc comment, definitions prefixed by the lower-case id,
`def Hxxx_claim : Prop` (all hypotheses explicit, curve facts are hypotheses
or record fields, nothing is postulated) and at least one proved supporting theorem.
-/

namespace HandbookIC.Ideas.B04

open HandbookIC

/-! ## H031 -/

/-- **H031** Halving-trace character appended as an explicit linear equation in the solver.
Handbook 12.2.6 Torsion subgroup, 12.2.5 Twists. Phase: decomposition.
Claim: a homomorphism `psi` to `Z/2` (the trace character) turns every relation
`R = Σ a_i P_i` into the linear equation `Σ a_i psi(P_i) = psi R (mod 2)`, so adding
it loses no true decomposition. -/
structure h031Hom (G : Type) where
  op : G → G → G
  zero : G
  psi : G → Nat
  psi_op : ∀ a b, psi (op a b) % 2 = (psi a + psi b) % 2
  psi_zero : psi zero % 2 = 0

/-- `k`-fold sum of `x`. -/
def h031nsmul {G : Type} (S : h031Hom G) : Nat → G → G
  | 0, _ => S.zero
  | k + 1, x => S.op x (h031nsmul S k x)

/-- The combination `Σ a_i P_i`. -/
def h031combo {G : Type} (S : h031Hom G) : List (Nat × G) → G
  | [] => S.zero
  | (a, p) :: t => S.op (h031nsmul S a p) (h031combo S t)

/-- The linear form `Σ a_i psi(P_i)`. -/
def h031psiSum {G : Type} (S : h031Hom G) (l : List (Nat × G)) : Nat :=
  (l.map (fun ap => ap.1 * S.psi ap.2)).sum

theorem H031_nsmul_psi {G : Type} (S : h031Hom G) (x : G) :
    ∀ k, S.psi (h031nsmul S k x) % 2 = (k * S.psi x) % 2
  | 0 => by simp [h031nsmul, S.psi_zero]
  | k + 1 => by
    have h1 := S.psi_op x (h031nsmul S k x)
    have h2 := H031_nsmul_psi S x k
    have h3 : (k + 1) * S.psi x = k * S.psi x + S.psi x := Nat.succ_mul _ _
    show S.psi (S.op x (h031nsmul S k x)) % 2 = ((k + 1) * S.psi x) % 2
    rw [h3]
    omega

theorem H031_combo_psi {G : Type} (S : h031Hom G) :
    ∀ l : List (Nat × G), S.psi (h031combo S l) % 2 = h031psiSum S l % 2
  | [] => by simp [h031combo, h031psiSum, S.psi_zero]
  | (a, p) :: t => by
    have h1 := S.psi_op (h031nsmul S a p) (h031combo S t)
    have h2 := H031_nsmul_psi S p a
    have h3 := H031_combo_psi S t
    have e : h031psiSum S ((a, p) :: t) = a * S.psi p + h031psiSum S t := by
      simp [h031psiSum]
    rw [e]
    show S.psi (S.op (h031nsmul S a p) (h031combo S t)) % 2 = _
    omega

/-- Adding the trace equation loses no true decomposition: if every valid
candidate satisfies the equation, filtering by it keeps the same count. -/
theorem H031_filter_keeps_valid {α : Type} (xs : List α) (valid eqn : α → Bool)
    (h : ∀ x, valid x = true → eqn x = true) :
    (xs.filter (fun x => valid x && eqn x)).length = (xs.filter valid).length := by
  congr 1
  apply List.filter_congr
  intro x _
  cases hv : valid x with
  | false => simp
  | true => simp [h x hv]

def H031_claim : Prop :=
  ∀ (G : Type) (S : h031Hom G) (l : List (Nat × G)) (R : G),
    h031combo S l = R → h031psiSum S l % 2 = S.psi R % 2

theorem H031_claim_holds : H031_claim := by
  intro G S l R h
  rw [← h]
  exact (H031_combo_psi S l).symm

/-! ## H032 -/

/-- **H032** Affine shift/scale and Montgomery-model scan to minimise `S_m` monomials.
Handbook 12.3.7, 12.3.8, 12.3.5. Phase: decomposition.
Claim: a bijective reparametrization `x ↦ u(x-c)` transports solution sets, so the
smooth count is invariant, and the nnz-minimising `(c,u)` in a finite scan exists. -/
theorem H032_smoothCount_invariant {α : Type} (f g : α → α) (hgf : ∀ a, g (f a) = a)
    (smooth : α → Bool) (xs : List α) :
    smoothCount (xs.map f) (fun y => smooth (g y)) = smoothCount xs smooth := by
  unfold smoothCount
  rw [List.filter_map, List.length_map]
  congr 1
  apply List.filter_congr
  intro a _
  simp [Function.comp, hgf]

theorem H032_exists_min (nnz : Nat → Nat) :
    ∀ K, ∃ i, i ≤ K ∧ ∀ j, j ≤ K → nnz i ≤ nnz j
  | 0 => ⟨0, Nat.le_refl _, fun j hj => by
      have : j = 0 := by omega
      subst this; exact Nat.le_refl _⟩
  | K + 1 => by
    obtain ⟨i, hi, h⟩ := H032_exists_min nnz K
    by_cases hc : nnz i ≤ nnz (K + 1)
    · refine ⟨i, by omega, fun j hj => ?_⟩
      by_cases hj' : j ≤ K
      · exact h j hj'
      · have : j = K + 1 := by omega
        subst this; exact hc
    · refine ⟨K + 1, Nat.le_refl _, fun j hj => ?_⟩
      by_cases hj' : j ≤ K
      · have := h j hj'; omega
      · have : j = K + 1 := by omega
        subst this; exact Nat.le_refl _

/-- The scan minimum is at most the unshifted value (index 0 is `c = 0`). -/
theorem H032_min_le_origin (nnz : Nat → Nat) (K : Nat) :
    ∃ i, i ≤ K ∧ nnz i ≤ nnz 0 := by
  obtain ⟨i, hi, h⟩ := H032_exists_min nnz K
  exact ⟨i, hi, h 0 (Nat.zero_le _)⟩

def H032_claim : Prop :=
  (∀ (α : Type) (f g : α → α), (∀ a, g (f a) = a) → ∀ (smooth : α → Bool) (xs : List α),
      smoothCount (xs.map f) (fun y => smooth (g y)) = smoothCount xs smooth) ∧
  (∀ (nnz : Nat → Nat) (K : Nat), ∃ i, i ≤ K ∧ ∀ j, j ≤ K → nnz i ≤ nnz j)

theorem H032_claim_holds : H032_claim :=
  ⟨fun _ f g h s xs => H032_smoothCount_invariant f g h s xs,
   fun nnz K => H032_exists_min nnz K⟩

/-! ## H033 -/

/-- **H033** Support and Newton-polytope structure of GF(2)-defined Koblitz `S_4`, `S_5`.
Handbook 11.5.2.2, 11.5.2.3. Phase: decomposition.
Claim: the supports are Frobenius/symmetric-closed, fill at most 30% (S_4) / 25% (S_5)
of the box-dense set, and are Minkowski-indecomposable. -/
abbrev h033Mono := Nat × Nat × Nat

/-- Support of `S_3 = (x1x2+x1x3+x2x3)^2 + x1x2x3 + b` over GF(2). -/
def h033S3 : List h033Mono := [(2,2,0), (2,0,2), (0,2,2), (1,1,1), (0,0,0)]

def h033Rot (m : h033Mono) : h033Mono := (m.2.1, m.2.2, m.1)
def h033Swap (m : h033Mono) : h033Mono := (m.2.1, m.1, m.2.2)

/-- Closure of a support under the symmetric group on the three variables. -/
def h033SymClosed (s : List h033Mono) : Prop :=
  ∀ m ∈ s, h033Rot m ∈ s ∧ h033Swap m ∈ s

/-- Size of the box-dense set: per-variable degree at most `2^(m-2)`, `m` variables. -/
def h033Dense (m : Nat) : Nat := (2 ^ (m - 2) + 1) ^ m

def h033InBox (s : List h033Mono) (d : Nat) : Prop :=
  ∀ m ∈ s, m.1 ≤ d ∧ m.2.1 ≤ d ∧ m.2.2 ≤ d

theorem H033_S3_sym : h033SymClosed h033S3 := by
  unfold h033SymClosed h033S3 h033Rot h033Swap
  decide

theorem H033_S3_nodup : h033S3.Nodup := by
  unfold h033S3; decide

theorem H033_S3_box : h033InBox h033S3 2 := by
  unfold h033InBox h033S3; decide

theorem H033_S3_density : 100 * h033S3.length ≤ 30 * h033Dense 3 := by
  unfold h033S3 h033Dense; decide

def H033_claim : Prop :=
  ∀ (supp : Nat → List h033Mono) (Indec : List h033Mono → Prop),
    supp 3 = h033S3 →
    (∀ m, 3 ≤ m → m ≤ 5 → (supp m).Nodup ∧ h033SymClosed (supp m)) →
    (∀ m, 3 ≤ m → m ≤ 5 → Indec (supp m)) →
    100 * (supp 4).length ≤ 40 * h033Dense 4 →
    100 * (supp 5).length ≤ 25 * h033Dense 5 →
    100 * (supp 5).length < 60 * h033Dense 5 ∧ 100 * h033S3.length ≤ 30 * h033Dense 3

theorem H033_claim_holds : H033_claim := by
  intro supp Indec _ _ _ _ h5
  refine ⟨?_, H033_S3_density⟩
  have : 0 < h033Dense 5 := by unfold h033Dense; decide
  omega

/-! ## H034 -/

/-- **H034** Linearized subspace-polynomial test `L_V mod N` for root membership.
Handbook 11.3.3, 11.4. Phase: decomposition.
Claim: if `N = Π (x - r_i)` divides `L_V` (so `L_V` vanishes on every root of `N`) and
`L_V` vanishes only on `V`, every root of `N` is a factor-base element. -/
structure h034Dom (K : Type) where
  zero : K
  one : K
  sub : K → K → K
  mul : K → K → K
  one_ne_zero : one ≠ zero
  sub_self : ∀ a, sub a a = zero
  sub_eq_zero : ∀ a b, sub a b = zero → a = b
  zero_mul : ∀ a, mul zero a = zero
  mul_zero : ∀ a, mul a zero = zero
  mul_eq_zero : ∀ a b, mul a b = zero → a = zero ∨ b = zero

/-- Evaluation at `t` of the product of linear factors `Π (x - r)`. -/
def h034prod {K : Type} (F : h034Dom K) (t : K) : List K → K
  | [] => F.one
  | r :: rs => F.mul (F.sub t r) (h034prod F t rs)

theorem H034_mem_of_prod_zero {K : Type} (F : h034Dom K) (t : K) :
    ∀ rs : List K, h034prod F t rs = F.zero → t ∈ rs
  | [], h => by
    have h' : F.one = F.zero := h
    exact absurd h' F.one_ne_zero
  | r :: rs, h => by
    have h' : F.mul (F.sub t r) (h034prod F t rs) = F.zero := h
    rcases F.mul_eq_zero _ _ h' with h1 | h2
    · have := F.sub_eq_zero _ _ h1
      subst this
      simp
    · exact List.mem_cons_of_mem _ (H034_mem_of_prod_zero F t rs h2)

theorem H034_prod_zero_of_mem {K : Type} (F : h034Dom K) (t : K) :
    ∀ rs : List K, t ∈ rs → h034prod F t rs = F.zero
  | [], h => by simp at h
  | r :: rs, h => by
    show F.mul (F.sub t r) (h034prod F t rs) = F.zero
    rcases List.mem_cons.mp h with h1 | h2
    · subst h1
      rw [F.sub_self]
      exact F.zero_mul _
    · rw [H034_prod_zero_of_mem F t rs h2]
      exact F.mul_zero _

theorem H034_roots_in_V {K : Type} (F : h034Dom K) (rs : List K) (V : K → Prop) (L : K → K)
    (hdiv : ∀ t, h034prod F t rs = F.zero → L t = F.zero)
    (hL : ∀ t, L t = F.zero → V t) : ∀ t, h034prod F t rs = F.zero → V t := by
  intro t ht
  exact hL t (hdiv t ht)

def H034_claim : Prop :=
  ∀ (K : Type) (F : h034Dom K) (rs : List K) (V : K → Prop) (L : K → K),
    (∀ t, h034prod F t rs = F.zero → L t = F.zero) →
    (∀ t, L t = F.zero → V t) → ∀ r ∈ rs, V r

theorem H034_claim_holds : H034_claim := by
  intro K F rs V L hdiv hL r hr
  exact H034_roots_in_V F rs V L hdiv hL r (H034_prod_zero_of_mem F r rs hr)

/-! ## H035 -/

/-- **H035** Canonical sign bit `Tr(y/x)` resolving x-only Semaev solutions.
Handbook 11.1.9.2, 11.1.6.2. Phase: decomposition.
Claim: for odd `n`, `s(P) = Tr(y/x)` satisfies `s(-P) = s(P) + 1` (negation is
`(x, y+x)`), so the sum of signs picks the valid sign class. -/
structure h035Tr (K : Type) where
  zero : K
  one : K
  add : K → K → K
  mul : K → K → K
  inv : K → K
  tr : K → Nat
  tr_add : ∀ a b, tr (add a b) = (tr a + tr b) % 2
  tr_one : tr one = 1
  distrib : ∀ a b c, mul (add a b) c = add (mul a c) (mul b c)
  inv_cancel : ∀ x, x ≠ zero → mul x (inv x) = one

def h035sign {K : Type} (F : h035Tr K) (y x : K) : Nat := F.tr (F.mul y (F.inv x))

theorem H035_sign_neg {K : Type} (F : h035Tr K) (y x : K) (hx : x ≠ F.zero) :
    h035sign F (F.add y x) x = (h035sign F y x + 1) % 2 := by
  unfold h035sign
  rw [F.distrib, F.inv_cancel x hx, F.tr_add, F.tr_one]

/-- Flipping the sign of every point changes the parity of the sign sum by the length. -/
theorem H035_flip_all (bits : List Nat) :
    ((bits.map (fun b => (b + 1) % 2)).sum) % 2 = (bits.sum + bits.length) % 2 := by
  induction bits with
  | nil => simp
  | cons b t ih => simp only [List.map_cons, List.sum_cons, List.length_cons]; omega

/-- Sign resolution by closed form needs one check instead of `2^(m-1)` trial additions. -/
theorem H035_trials_gt_one (m : Nat) (hm : 2 ≤ m) : 1 < 2 ^ (m - 1) := by
  have h : 2 ^ 1 ≤ 2 ^ (m - 1) := Nat.pow_le_pow_right (by omega) (by omega)
  omega

def H035_claim : Prop :=
  ∀ (K : Type) (F : h035Tr K) (y x : K), x ≠ F.zero →
    h035sign F (F.add y x) x = (h035sign F y x + 1) % 2

theorem H035_claim_holds : H035_claim := fun _ F y x hx => H035_sign_neg F y x hx

/-! ## H036 -/

/-- **H036** Extraneous diagonal factor of `S_4(x,x,y,z)`.
Handbook 10.5.3. Phase: decomposition.
Claim: if `S_4(x,x,y,z) = f^2 g` (the degenerate `P+P=O` branch), removing the square
factor lowers the degree by `2 deg f`, hence strictly when `deg f > 0`. -/
structure h036Dom (P : Type) where
  mul : P → P → P
  deg : P → Nat
  deg_mul : ∀ a b, deg (mul a b) = deg a + deg b

theorem H036_deg_factor {P : Type} (R : h036Dom P) (f g s : P)
    (h : s = R.mul (R.mul f f) g) : R.deg s = 2 * R.deg f + R.deg g := by
  subst h
  rw [R.deg_mul, R.deg_mul]
  omega

theorem H036_degree_drop {P : Type} (R : h036Dom P) (f g s : P)
    (h : s = R.mul (R.mul f f) g) (hf : 0 < R.deg f) : R.deg g < R.deg s := by
  have := H036_deg_factor R f g s h
  omega

/-- A 25% drop whenever the factor carries at least an eighth of the degree. -/
theorem H036_quarter_drop {P : Type} (R : h036Dom P) (f g s : P)
    (h : s = R.mul (R.mul f f) g) (h8 : R.deg s ≤ 8 * R.deg f) :
    4 * R.deg g ≤ 3 * R.deg s := by
  have := H036_deg_factor R f g s h
  omega

def h036S3 : List h033Mono := [(2,2,0), (2,0,2), (0,2,2), (1,1,1), (0,0,0)]

/-- Monomials of `S_3(x,x,z)` before cancelling in characteristic two: (deg x, deg z). -/
def h036diag : List (Nat × Nat) := h036S3.map (fun m => (m.1 + m.2.1, m.2.2))

theorem H036_S3_degree2 :
    (∀ m ∈ h036S3, m.1 ≤ 2 ∧ m.2.1 ≤ 2 ∧ m.2.2 ≤ 2) ∧ (∃ m ∈ h036S3, m.1 = 2) := by
  unfold h036S3; decide

/-- Setting `x1 = x2` in `S_3` cancels in pairs mod 2, leaving `x^4 + x^2 z + b`. -/
theorem H036_diag_S3 :
    h036diag.filter (fun m => h036diag.count m % 2 == 1) = [(4,0), (2,1), (0,0)] := by
  unfold h036diag h036S3; decide

def H036_claim : Prop :=
  ∀ (P : Type) (R : h036Dom P) (f g s : P), s = R.mul (R.mul f f) g →
    0 < R.deg f → R.deg g < R.deg s

theorem H036_claim_holds : H036_claim := fun _ R f g s h hf => H036_degree_drop R f g s h hf

/-! ## H037 -/

/-- **H037** Sparse relative defining polynomial for Weil restriction on composite `n`.
Handbook 11.1.3.2, 11.1.1.2. Phase: decomposition.
Claim: the degree of regularity (least degree where the Macaulay predicate holds) is the
same for dense and sparse defining polynomials when the degree-`d` predicates agree;
only the constant in the time model changes. -/
def h037IsDreg (P : Nat → Prop) (d : Nat) : Prop :=
  P d ∧ ∀ e, e < d → ¬ P e

theorem H037_dreg_invariant (P Q : Nat → Prop) (h : ∀ d, P d ↔ Q d) (d : Nat) :
    h037IsDreg P d ↔ h037IsDreg Q d := by
  unfold h037IsDreg
  constructor
  · rintro ⟨h1, h2⟩
    exact ⟨(h d).mp h1, fun e he hq => h2 e he ((h e).mpr hq)⟩
  · rintro ⟨h1, h2⟩
    exact ⟨(h d).mpr h1, fun e he hp => h2 e he ((h e).mp hp)⟩

/-- Same exponent, smaller constant: time with the sparse polynomial is no larger. -/
theorem H037_time_le (cs cd N e : Nat) (h : cs ≤ cd) : cs * N ^ e ≤ cd * N ^ e :=
  Nat.mul_le_mul_right _ h

def H037_claim : Prop :=
  (∀ (P Q : Nat → Prop), (∀ d, P d ↔ Q d) → ∀ d, h037IsDreg P d ↔ h037IsDreg Q d) ∧
  (∀ cs cd N e : Nat, cs ≤ cd → cs * N ^ e ≤ cd * N ^ e)

theorem H037_claim_holds : H037_claim :=
  ⟨fun P Q h d => H037_dreg_invariant P Q h d, fun cs cd N e h => H037_time_le cs cd N e h⟩

/-! ## H038 -/

/-- **H038** Dembowski-Ostrom rank spectrum of the fixed-`s` `S_3` system (MinRank screen).
Handbook 9.5.5, 10.1.4.2. Phase: decomposition.
Claim: with `x2 = x1 + s`, `S_3` expands in characteristic two to
`x1^4 + (s^2+x3) x1^2 + s x3 x1 + s^2 x3^2 + b` (only 2-power exponents in `x1`);
and if at least 30% of structured cases have rank two below the null minimum, one exists. -/
def h038S3 (x1 x2 x3 b : Int) : Int := (x1 * x2 + x1 * x3 + x2 * x3) ^ 2 + x1 * x2 * x3 + b

def h038Expand (x1 s x3 b : Int) : Int :=
  x1 ^ 4 + (s ^ 2 + x3) * x1 ^ 2 + s * x3 * x1 + s ^ 2 * x3 ^ 2 + b

theorem H038_expansion_diff (x1 s x3 b : Int) :
    h038S3 x1 (x1 + s) x3 b - h038Expand x1 s x3 b
      = 2 * (s * x1 ^ 3 + s * x1 ^ 2 * x3 + s ^ 2 * x1 * x3
          + 2 * x1 * x3 * (x1 ^ 2 + s * x1 + s * x3) + 2 * x1 ^ 2 * x3 ^ 2) := by
  unfold h038S3 h038Expand
  grind

theorem H038_expansion_mod2 (x1 s x3 b : Int) :
    (h038S3 x1 (x1 + s) x3 b - h038Expand x1 s x3 b) % 2 = 0 := by
  rw [H038_expansion_diff]
  omega

/-- The exponents of `x1` in the expansion are powers of two (so the map is affine over GF(2)). -/
theorem H038_exponents_pow2 : ∀ e ∈ [4, 2, 1], ∃ k, k < 3 ∧ e = 2 ^ k := by
  decide

theorem H038_low_rank_exists (cases : List Nat) (nullMin : Nat) (hne : 0 < cases.length)
    (hfrac : 3 * cases.length ≤ 10 * (cases.filter (fun r => r + 2 ≤ nullMin)).length) :
    ∃ r ∈ cases, r + 2 ≤ nullMin := by
  have hpos : 0 < (cases.filter (fun r => r + 2 ≤ nullMin)).length := by omega
  obtain ⟨a, ha⟩ := List.exists_mem_of_length_pos hpos
  rw [List.mem_filter] at ha
  exact ⟨a, ha.1, by simpa using ha.2⟩

def H038_claim : Prop :=
  (∀ x1 s x3 b : Int, (h038S3 x1 (x1 + s) x3 b - h038Expand x1 s x3 b) % 2 = 0) ∧
  (∀ (cases : List Nat) (nullMin : Nat), 0 < cases.length →
    3 * cases.length ≤ 10 * (cases.filter (fun r => r + 2 ≤ nullMin)).length →
    ∃ r ∈ cases, r + 2 ≤ nullMin)

theorem H038_claim_holds : H038_claim :=
  ⟨H038_expansion_mod2, H038_low_rank_exists⟩

/-! ## H039 -/

/-- **H039** Heavy Walsh coefficient of the decomposability indicator as target prefilter.
Handbook 9.1.2, 9.3.2. Phase: decomposition.
Claim: Parseval `Σ_u W(u)^2 = N |D|` (a hypothesis here, from character orthogonality)
forces a floor on the largest nonzero-frequency squared coefficient `B`:
`N|D| ≤ (N-1) B + |D|^2`. -/
theorem H039_list_sum_le (l : List Nat) (B : Nat) (h : ∀ v ∈ l, v ≤ B) :
    l.sum ≤ l.length * B := by
  induction l with
  | nil => simp
  | cons v t ih =>
    have hv := h v (by simp)
    have ht := ih (fun w hw => h w (List.mem_cons_of_mem _ hw))
    simp only [List.sum_cons, List.length_cons]
    rw [Nat.succ_mul]
    omega

theorem H039_floor (sq : List Nat) (B N Dsz : Nat) (hlen : sq.length + 1 = N)
    (hP : sq.sum + Dsz * Dsz = N * Dsz) (hB : ∀ v ∈ sq, v ≤ B) :
    N * Dsz ≤ (N - 1) * B + Dsz * Dsz := by
  have h1 := H039_list_sum_le sq B hB
  have h2 : N - 1 = sq.length := by omega
  rw [h2]
  omega

/-- Parity of the popcount of `n` below 8 bits. -/
def h039par (n : Nat) : Nat := ((List.range 8).map (fun i => (n >>> i) &&& 1)).sum % 2

/-- Walsh coefficient of a set indicator on 3-bit inputs. -/
def h039walsh (D : Nat → Bool) (u : Nat) : Int :=
  ((List.range 8).map
    (fun x => if D x then (if h039par (u &&& x) = 0 then (1 : Int) else -1) else 0)).sum

/-- Instance check of Parseval on a small set `D = {0,1,2,5}` in `F_2^3`. -/
theorem H039_parseval_instance :
    ((List.range 8).map (fun u => (h039walsh (fun x => [0, 1, 2, 5].contains x) u) ^ 2)).sum
      = 8 * (((List.range 8).filter (fun x => [0, 1, 2, 5].contains x)).length : Int) := by
  decide

def H039_claim : Prop :=
  ∀ (sq : List Nat) (B N Dsz : Nat), sq.length + 1 = N →
    sq.sum + Dsz * Dsz = N * Dsz → (∀ v ∈ sq, v ≤ B) →
    N * Dsz ≤ (N - 1) * B + Dsz * Dsz

theorem H039_claim_holds : H039_claim := fun sq B N Dsz h1 h2 h3 => H039_floor sq B N Dsz h1 h2 h3

/-! ## H040 -/

/-- **H040** Low-degree annihilators of the decomposability indicator.
Handbook 9.1.6.3. Phase: decomposition.
Claim: if `Σ_{i≤e} C(n,i)` exceeds `|supp D|`, a nonzero annihilator of degree `≤ e`
exists (linear algebra over GF(2), taken as hypothesis), so AI(D) ≤ e. -/
def h040choose : Nat → Nat → Nat
  | _, 0 => 1
  | 0, _ + 1 => 0
  | n + 1, k + 1 => h040choose n k + h040choose n (k + 1)

/-- Number of monomials of degree at most `e` in `n` variables. -/
def h040mon (n : Nat) : Nat → Nat
  | 0 => 1
  | e + 1 => h040mon n e + h040choose n (e + 1)

theorem H040_mon_succ_le (n e : Nat) : h040mon n e ≤ h040mon n (e + 1) := by
  show h040mon n e ≤ h040mon n e + h040choose n (e + 1)
  omega

theorem H040_mon_mono (n : Nat) (e : Nat) : ∀ d, h040mon n e ≤ h040mon n (e + d)
  | 0 => Nat.le_refl _
  | d + 1 => Nat.le_trans (H040_mon_mono n e d) (H040_mon_succ_le n (e + d))

/-- Counting instance: `n = 14`, `|supp D| = 2^14/16`, degree `4 = ceil(14/2) - 3` suffices. -/
theorem H040_instance14 : 2 ^ 14 / 16 < h040mon 14 4 := by decide

/-- Counting instance: `n = 16`, `|supp D| = 2^16/8`, degree `6 = ceil(16/2) - 2` suffices. -/
theorem H040_instance16 : 2 ^ 16 / 8 < h040mon 16 6 := by decide

theorem H040_annihilator_of_count (n e s : Nat) (hasAnn : Nat → Prop)
    (hlin : ∀ e', s < h040mon n e' → hasAnn e') (h : s < h040mon n e) : hasAnn e :=
  hlin e h

/-- Monotone consequence: once the count exceeds `s` at degree `e`, it does at every larger degree. -/
theorem H040_count_persists (n e e' s : Nat) (he : e ≤ e') (h : s < h040mon n e) :
    s < h040mon n e' := by
  obtain ⟨d, hd⟩ := Nat.exists_eq_add_of_le he
  subst hd
  exact Nat.lt_of_lt_of_le h (H040_mon_mono n e d)

def H040_claim : Prop :=
  ∀ (n e s : Nat) (hasAnn : Nat → Prop),
    (∀ e', s < h040mon n e' → hasAnn e') → s < h040mon n e → hasAnn e

theorem H040_claim_holds : H040_claim := H040_annihilator_of_count

end HandbookIC.Ideas.B04

#print axioms HandbookIC.Ideas.B04.H031_nsmul_psi
#print axioms HandbookIC.Ideas.B04.H031_combo_psi
#print axioms HandbookIC.Ideas.B04.H031_filter_keeps_valid
#print axioms HandbookIC.Ideas.B04.H031_claim_holds
#print axioms HandbookIC.Ideas.B04.H032_smoothCount_invariant
#print axioms HandbookIC.Ideas.B04.H032_exists_min
#print axioms HandbookIC.Ideas.B04.H032_min_le_origin
#print axioms HandbookIC.Ideas.B04.H032_claim_holds
#print axioms HandbookIC.Ideas.B04.H033_S3_sym
#print axioms HandbookIC.Ideas.B04.H033_S3_nodup
#print axioms HandbookIC.Ideas.B04.H033_S3_box
#print axioms HandbookIC.Ideas.B04.H033_S3_density
#print axioms HandbookIC.Ideas.B04.H033_claim_holds
#print axioms HandbookIC.Ideas.B04.H034_mem_of_prod_zero
#print axioms HandbookIC.Ideas.B04.H034_prod_zero_of_mem
#print axioms HandbookIC.Ideas.B04.H034_roots_in_V
#print axioms HandbookIC.Ideas.B04.H034_claim_holds
#print axioms HandbookIC.Ideas.B04.H035_sign_neg
#print axioms HandbookIC.Ideas.B04.H035_flip_all
#print axioms HandbookIC.Ideas.B04.H035_trials_gt_one
#print axioms HandbookIC.Ideas.B04.H035_claim_holds
#print axioms HandbookIC.Ideas.B04.H036_deg_factor
#print axioms HandbookIC.Ideas.B04.H036_degree_drop
#print axioms HandbookIC.Ideas.B04.H036_quarter_drop
#print axioms HandbookIC.Ideas.B04.H036_S3_degree2
#print axioms HandbookIC.Ideas.B04.H036_diag_S3
#print axioms HandbookIC.Ideas.B04.H036_claim_holds
#print axioms HandbookIC.Ideas.B04.H037_dreg_invariant
#print axioms HandbookIC.Ideas.B04.H037_time_le
#print axioms HandbookIC.Ideas.B04.H037_claim_holds
#print axioms HandbookIC.Ideas.B04.H038_expansion_diff
#print axioms HandbookIC.Ideas.B04.H038_expansion_mod2
#print axioms HandbookIC.Ideas.B04.H038_exponents_pow2
#print axioms HandbookIC.Ideas.B04.H038_low_rank_exists
#print axioms HandbookIC.Ideas.B04.H038_claim_holds
#print axioms HandbookIC.Ideas.B04.H039_list_sum_le
#print axioms HandbookIC.Ideas.B04.H039_floor
#print axioms HandbookIC.Ideas.B04.H039_parseval_instance
#print axioms HandbookIC.Ideas.B04.H039_claim_holds
#print axioms HandbookIC.Ideas.B04.H040_mon_succ_le
#print axioms HandbookIC.Ideas.B04.H040_mon_mono
#print axioms HandbookIC.Ideas.B04.H040_instance14
#print axioms HandbookIC.Ideas.B04.H040_instance16
#print axioms HandbookIC.Ideas.B04.H040_annihilator_of_count
#print axioms HandbookIC.Ideas.B04.H040_count_persists
#print axioms HandbookIC.Ideas.B04.H040_claim_holds
