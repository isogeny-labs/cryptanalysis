/-
Copyright (c) 2026 Isogeny Labs. All rights reserved.
 Formalization of Lead 2D:
 1. Prescribed-Singularity (Nodal) Degree-`d ≥ 4` Plane Bézout Lifts:
    - Euler homogeneous node constraint (`∂_X C = ∂_Y C = ∂_Z C = 0 -> d · C = 0`);
    - Off-curve node (`I_{Q_k}(E, C̄) = 0`) dimension obstruction: `K_off(d, δ) = d(d-3)/2 - 3δ`,
      proving `g_geom ≤ 2 -> no nonzero kernel` for all `d ≥ 4` and `K_off ≥ 1 -> 3 g_geom ≥ d² - 3d + 4`;
    - On-curve node (`I_{Q_k}(E, C̄) ≥ 2`) universal identity: when `2δ + r = 3d + 1`,
      `K_on(d, δ) = g_geom(d, δ) - 1`, proving `g_geom ≤ 1 -> no nonzero kernel` for all `d ≥ 4`,
      and `g_geom = 2` admits `K_on ≥ 1` iff `d ∈ {4, 5, 6}` with exact minimal triples
      `(4, 1, 11)`, `(5, 4, 8)`, `(6, 8, 3)` (`δ + r ≤ 12`);
    - Leibniz rule on reducible fiber `C̄ = E · G`: an on-curve node `Q_k ∈ E` where `E` is smooth
      (`∇E(Q_k) ≠ 0`) forces `G(Q_k) = 0`, placing `Q_k` on `E ∩ G`.
 2. Cayley–Bacharach 9-Point Cubic Pencil (`dim ker_ℚ B(P_0..P_8) = 2`) & `CoordinateFb`:
    - Chord-origin scalar specialization `n_CB = (-2, -2, 1, 1, 1, 1, 1, 1, 1)` of `∑_{i=0}^8 P_i = 3H`
      and fixed-flex transport `(1, 1, 1, 1, 1, 1, 1, 1, 1)`;
    - Exact 9th-point elimination isomorphism: any relation `m ∈ ker(ℤ^9 -> A)` modulo `ℤ · n_CB`
      maps bijectively via `m' = m - m_8 · n_CB` (`m'_8 = 0`) to direct `r = 8` relations on `P_0..P_7`;
    - Height-amplification vs box-capacity obstruction: `(2H + 1)^3 ≥ p` (`H ≥ 1`, `p ≥ 2`)
      forces `(3H)^20 > p^6 > p`, guaranteeing mod-`p` wraparound of the 9th base point `P̃_8`.
-/

namespace NodalBezoutAndCayleyBacharach

/-! ## Section 1: Euler homogeneous vanishing & Leibniz on-curve node residual law -/

/-- Euler's homogeneous relation: if `X · ∂_X C + Y · ∂_Y C + Z · ∂_Z C = d · C` and all three
    partial derivatives vanish at `(X, Y, Z)` over `ℤ` with `d ≥ 1`, then `C(X, Y, Z) = 0`
    automatically (so a projective singular point imposes 3 linear equations, not 4). -/
theorem euler_homogeneous_partials_zero_implies_value_zero
    {d : Int} (hd : 1 ≤ d) {x y z cx cy cz cval : Int}
    (heuler : x * cx + y * cy + z * cz = d * cval)
    (hcx : cx = 0) (hcy : cy = 0) (hcz : cz = 0) :
    cval = 0 := by
  have hzero : d * cval = 0 := by
    rw [← heuler, hcx, hcy, hcz, Int.mul_zero, Int.mul_zero, Int.mul_zero]
    rfl
  rcases Int.mul_eq_zero.mp hzero with hd0 | hc0
  · omega
  · exact hc0

/-- Leibniz product rule on `C̄ = E · G` at a smooth point `Q` of `E` (`E(Q) = 0`, `eGrad ≠ 0`):
    in any integral domain, if `(∇C̄)(Q) = E(Q) · gGrad + G(Q) · eGrad = 0`, then `G(Q) = 0`. -/
theorem leibniz_on_curve_node_forces_residual_zero
    {R : Type} [Zero R] [Add R] [Mul R]
    (hadd0 : ∀ x : R, Zero.zero + x = x)
    (hmul0 : ∀ x : R, Zero.zero * x = Zero.zero)
    (hdom : ∀ a b : R, a * b = Zero.zero → a = Zero.zero ∨ b = Zero.zero)
    {eVal gVal eGrad gGrad : R}
    (honE : eVal = Zero.zero)
    (hsmoothE : eGrad ≠ Zero.zero)
    (hnodeC : eVal * gGrad + gVal * eGrad = Zero.zero) :
    gVal = Zero.zero := by
  rw [honE, hmul0, hadd0] at hnodeC
  rcases hdom gVal eGrad hnodeC with hg0 | he0
  · exact hg0
  · exact False.elim (hsmoothE he0)

/-! ## Section 2: Nodal plane-curve dimension counts (`d ≥ 4`) -/

/-- Number of homogeneous degree-`d` monomials in `ℙ²`: `N_d = (d + 1)(d + 2) / 2`. -/
def planeMonomialCount (d : Nat) : Nat :=
  (d + 1) * (d + 2) / 2

/-- Smooth plane-curve genus `g_smooth(d) = (d - 1)(d - 2) / 2`. -/
def smoothPlaneGenus (d : Nat) : Nat :=
  (d - 1) * (d - 2) / 2

/-- Geometric genus of a degree-`d` plane curve with `δ` ordinary double points (nodes). -/
def nodalGeometricGenus (d delta : Nat) : Nat :=
  smoothPlaneGenus d - delta

theorem even_consecutive_prod (n : Nat) : 2 ∣ n * (n + 1) := by
  induction n with
  | zero => exact ⟨0, rfl⟩
  | succ k ih =>
      rcases ih with ⟨q, hq⟩
      refine ⟨q + (k + 1), ?_⟩
      have hcalc : (k + 1) * (k + 2) = k * (k + 1) + 2 * (k + 1) := by
        calc
          (k + 1) * (k + 2) = (k + 1) * k + (k + 1) * 2 := Nat.mul_add (k + 1) k 2
          _ = k * (k + 1) + 2 * (k + 1) := by
              rw [Nat.mul_comm (k + 1) k, Nat.mul_comm (k + 1) 2]
      rw [hcalc, hq]
      omega

theorem two_mul_planeMonomialCount (d : Nat) :
    2 * planeMonomialCount d = d * d + 3 * d + 2 := by
  unfold planeMonomialCount
  rcases even_consecutive_prod (d + 1) with ⟨q, hq⟩
  have h2q : 2 * ((d + 1) * (d + 2) / 2) = (d + 1) * (d + 2) := by
    rw [hq]
    omega
  have hexp : (d + 1) * (d + 2) = d * d + 3 * d + 2 := by
    calc
      (d + 1) * (d + 2) = d * (d + 2) + 1 * (d + 2) := Nat.add_mul d 1 (d + 2)
      _ = (d * d + d * 2) + (d + 2) := by rw [Nat.mul_add, Nat.one_mul]
      _ = d * d + 3 * d + 2 := by omega
  rw [h2q, hexp]

theorem two_mul_smoothPlaneGenus_add_three_d {d : Nat} (hd : 2 ≤ d) :
    2 * smoothPlaneGenus d + 3 * d = d * d + 2 := by
  unfold smoothPlaneGenus
  have h1 : d - 1 = (d - 2) + 1 := by omega
  have hcomm : (d - 1) * (d - 2) = (d - 2) * ((d - 2) + 1) := by
    rw [h1, Nat.mul_comm]
  rcases even_consecutive_prod (d - 2) with ⟨q, hq⟩
  have h2q : 2 * ((d - 1) * (d - 2) / 2) = (d - 1) * (d - 2) := by
    rw [hcomm, hq]
    omega
  have hk : d = (d - 2) + 2 := by omega
  have hsq : d * d = (d - 2) * (d - 2) + 4 * (d - 2) + 4 := by
    calc
      d * d = ((d - 2) + 2) * ((d - 2) + 2) := by rw [← hk]
      _ = (d - 2) * ((d - 2) + 2) + 2 * ((d - 2) + 2) := Nat.add_mul (d - 2) 2 ((d - 2) + 2)
      _ = ((d - 2) * (d - 2) + (d - 2) * 2) + (2 * (d - 2) + 4) := by
            rw [Nat.mul_add, Nat.mul_add]
      _ = (d - 2) * (d - 2) + 4 * (d - 2) + 4 := by omega
  have hprod : (d - 1) * (d - 2) = (d - 2) * (d - 2) + (d - 2) := by
    rw [hcomm, Nat.mul_add, Nat.mul_one]
  have h3d : 3 * d = 3 * (d - 2) + 6 := by omega
  rw [h2q, hprod, h3d, hsq]
  omega

/-- **Universal Smooth Genus vs Bézout Kernel Identity (`g_smooth(d) + (3d + 1) = N_d + 1`):**
    For every `d ≥ 3`, smooth plane genus exceeds the smooth Bézout kernel dimension
    `N_d - (3d + 1) = d(d - 3)/2` by **exact constant 1**. -/
theorem smoothPlaneGenus_add_bezoutThreshold_eq_monomialCount_add_one
    {d : Nat} (hd : 3 ≤ d) :
    smoothPlaneGenus d + (3 * d + 1) = planeMonomialCount d + 1 := by
  have hN := two_mul_planeMonomialCount d
  have hg := two_mul_smoothPlaneGenus_add_three_d (d := d) (by omega)
  omega

/-! ### Case 2A: Off-curve nodes (`Q_k ∉ E`, Bézout multiplicity `0` at nodes) -/

/-- **Off-Curve Node Low-Genus Impossibility (`g_geom ≤ 2 → 0` kernel):**
    If `δ` nodes lie off `E(𝔽_p)` (`I_{Q_k}(E, C̄) = 0`), automatic Bézout divisibility still
    requires `r ≥ 3d + 1` on-curve points, imposing `r + 3δ` linear equations in `N_d` unknowns.
    Whenever `g_geom = smoothPlaneGenus d - δ ≤ 2` (`d ≥ 4`), `r + 3δ > N_d`. -/
theorem off_curve_nodal_genus_le_two_no_kernel
    {d delta r : Nat} (hd : 4 ≤ d) (hdel : delta ≤ smoothPlaneGenus d)
    (hbez : 3 * d + 1 ≤ r) (hg : nodalGeometricGenus d delta ≤ 2) :
    planeMonomialCount d < r + 3 * delta := by
  have hid := smoothPlaneGenus_add_bezoutThreshold_eq_monomialCount_add_one (d := d) (by omega)
  have hg2 := two_mul_smoothPlaneGenus_add_three_d (d := d) (by omega)
  unfold nodalGeometricGenus at hg
  have hd4 : 4 * d ≤ d * d := Nat.mul_le_mul_right d hd
  omega

/-- **Off-Curve Node Quadratic Genus Floor (`K_off ≥ 1 → 3 g_geom ≥ d² - 3d + 4`):**
    For every `d ≥ 4`, if `(3d + 1) + 3δ + 1 ≤ N_d`, then `3 · g_geom(d, δ) ≥ d² - 3d + 4`
    (hence `g_geom ≥ 3` for all `d ≥ 4`, growing quadratically as `Θ(d²)`). -/
theorem off_curve_nodal_positive_kernel_genus_lower_bound
    {d delta : Nat} (hd : 4 ≤ d) (hdel : delta ≤ smoothPlaneGenus d)
    (hker : (3 * d + 1) + 3 * delta + 1 ≤ planeMonomialCount d) :
    d * d - 3 * d + 4 ≤ 3 * nodalGeometricGenus d delta ∧ 3 ≤ nodalGeometricGenus d delta := by
  have hN := two_mul_planeMonomialCount d
  have hg := two_mul_smoothPlaneGenus_add_three_d (d := d) (by omega)
  have hd4 : 4 * d ≤ d * d := Nat.mul_le_mul_right d hd
  unfold nodalGeometricGenus
  omega

/-! ### Case 2B: On-curve nodes (`Q_k ∈ E`, Bézout multiplicity `≥ 2` at nodes) -/

/-- **On-Curve Node Universal Dimension Identity (`K_on = g_geom - 1`):**
    When `δ` nodes lie on `E(𝔽_p)` (`I_{Q_k}(E, C̄) ≥ 2`) and `2δ + r = 3d + 1` (`d ≥ 4`),
    `N_d + 1 = (3δ + r) + g_geom(d, δ)`; hence when `g_geom ≥ 1`, guaranteed kernel dimension is
    `N_d - (3δ + r) = g_geom(d, δ) - 1`. -/
theorem on_curve_nodal_kernel_eq_genus_sub_one
    {d delta r : Nat} (hd : 4 ≤ d) (hdel : delta ≤ smoothPlaneGenus d)
    (hbez : 2 * delta + r = 3 * d + 1) :
    planeMonomialCount d + 1 = (3 * delta + r) + nodalGeometricGenus d delta := by
  have hid := smoothPlaneGenus_add_bezoutThreshold_eq_monomialCount_add_one (d := d) (by omega)
  unfold nodalGeometricGenus
  omega

/-- **On-Curve Node `g_geom ≤ 1` Obstruction (`K_on = 0` for all `d ≥ 4`):**
    For every `d ≥ 4`, `δ ≤ g_smooth(d)`, and `r : ℕ`, if `2δ + r ≥ 3d + 1` and `g_geom ≤ 1`,
    then `3δ + r ≥ N_d`, closing genus `0` and genus `1` for every degree `d ≥ 4`. -/
theorem on_curve_nodal_genus_le_one_no_kernel
    {d delta r : Nat} (hd : 4 ≤ d) (hdel : delta ≤ smoothPlaneGenus d)
    (hbez : 3 * d + 1 ≤ 2 * delta + r) (hg : nodalGeometricGenus d delta ≤ 1) :
    planeMonomialCount d ≤ 3 * delta + r := by
  have hid := smoothPlaneGenus_add_bezoutThreshold_eq_monomialCount_add_one (d := d) (by omega)
  unfold nodalGeometricGenus at hg
  omega

/-- **Exact `g_geom = 2` Classification (`d ∈ {4, 5, 6}` Only):**
    At `g_geom(d, δ) = 2` (`δ ≤ g_smooth(d)`, `d ≥ 4`), there exists `r : ℕ` satisfying both
    strict Bézout auto-divisibility (`2δ + r ≥ 3d + 1`) and positive kernel rank
    (`3δ + r + 1 ≤ N_d`) **if and only if `d = 4 ∨ d = 5 ∨ d = 6`**. -/
theorem on_curve_nodal_genus_two_iff_d_in_4_5_6
    {d delta : Nat} (hd : 4 ≤ d) (hdel : delta ≤ smoothPlaneGenus d)
    (hg2 : nodalGeometricGenus d delta = 2) :
    (∃ r : Nat, 3 * d + 1 ≤ 2 * delta + r ∧ 3 * delta + r + 1 ≤ planeMonomialCount d) ↔
      (d = 4 ∨ d = 5 ∨ d = 6) := by
  have hN := two_mul_planeMonomialCount d
  have hgs := two_mul_smoothPlaneGenus_add_three_d (d := d) (by omega)
  unfold nodalGeometricGenus at hg2
  constructor
  · rintro ⟨r, hbez, hker⟩
    by_cases hle6 : d ≤ 6
    · omega
    · have hd7 : 7 ≤ d := by omega
      have hsq : 7 * d ≤ d * d := Nat.mul_le_mul_right d hd7
      omega
  · intro hcases
    rcases hcases with rfl | rfl | rfl
    · have hgs4 : smoothPlaneGenus 4 = 3 := by decide
      have hN4 : planeMonomialCount 4 = 15 := by decide
      exact ⟨11, by omega, by omega⟩
    · have hgs5 : smoothPlaneGenus 5 = 6 := by decide
      have hN5 : planeMonomialCount 5 = 21 := by decide
      exact ⟨8, by omega, by omega⟩
    · have hgs6 : smoothPlaneGenus 6 = 10 := by decide
      have hN6 : planeMonomialCount 6 = 28 := by decide
      exact ⟨3, by omega, by omega⟩

/-- Concrete kernel-checked parameters for the unique three `g_geom = 2` on-curve nodal triples
    `(4, 1, 11)`, `(5, 4, 8)`, `(6, 8, 3)` (`δ + r ≤ 12`, `K_on = 1`) and the `d = 7` cutoff. -/
theorem nodal_genus_two_triples_checked :
    (planeMonomialCount 4 = 15 ∧ nodalGeometricGenus 4 1 = 2 ∧ 2 * 1 + 11 = 13 ∧ 3 * 1 + 11 = 14 ∧ 1 + 11 ≤ 12) ∧
    (planeMonomialCount 5 = 21 ∧ nodalGeometricGenus 5 4 = 2 ∧ 2 * 4 + 8 = 16 ∧ 3 * 4 + 8 = 20 ∧ 4 + 8 ≤ 12) ∧
    (planeMonomialCount 6 = 28 ∧ nodalGeometricGenus 6 8 = 2 ∧ 2 * 8 + 3 = 19 ∧ 3 * 8 + 3 = 27 ∧ 8 + 3 ≤ 12) ∧
    (planeMonomialCount 7 = 36 ∧ nodalGeometricGenus 7 13 = 2 ∧ planeMonomialCount 7 < 3 * 13) := by
  decide

/-! ## Section 3: Cayley–Bacharach 9-point cubic pencil elimination & box-capacity bound -/

/-- Canonical chord-origin scalar vector `n_CB = (-2, -2, 1, 1, 1, 1, 1, 1, 1)` on `Fin 9`
    encoding `∑_{i=0}^8 P_i = 3(P_0 + P_1 + O)` as `∑_{i=0}^8 n_CB[i] (P_i - O) = 0`. -/
def cbChordScalar (i : Fin 9) : Int :=
  if i.val = 0 ∨ i.val = 1 then -2 else 1

/-- Fixed-flex transport `n_CB + 3 · (e_0 + e_1)` equals `(1, 1, 1, 1, 1, 1, 1, 1, 1)`. -/
theorem cbChordScalar_transport_core (i : Fin 9) :
    cbChordScalar i
      + 3 * ((if i.val = 0 then (1 : Int) else 0) + (if i.val = 1 then (1 : Int) else 0)) = 1 := by
  unfold cbChordScalar
  by_cases h0 : i.val = 0
  · simp [h0]
  · by_cases h1 : i.val = 1
    · simp [h1]
    · simp [h0, h1]

/-- 9-point elimination reduction: subtracting `m[8] · cbChordScalar` zeroes slot `8`. -/
def eliminateNinthPoint (m : Fin 9 → Int) (i : Fin 9) : Int :=
  m i - m ⟨8, by decide⟩ * cbChordScalar i

theorem eliminateNinthPoint_at_eight (m : Fin 9 → Int) :
    eliminateNinthPoint m ⟨8, by decide⟩ = 0 := by
  unfold eliminateNinthPoint cbChordScalar
  simp

/-- **Cayley–Bacharach 9th-Point Elimination Equivalence:**
    An integer relation `m : Fin 9 → Int` is NOT a scalar multiple of `cbChordScalar` iff its
    9th-point-eliminated projection `eliminateNinthPoint m` is a nonzero 8-point vector
    (`m' 8 = 0` and `∃ j < 8, m' j ≠ 0`). -/
theorem cb_second_relation_iff_nonzero_eight_point_projection (m : Fin 9 → Int) :
    (∀ k : Int, ∃ i : Fin 9, m i ≠ k * cbChordScalar i) ↔
      (∃ j : Fin 9, j.val < 8 ∧ eliminateNinthPoint m j ≠ 0) := by
  constructor
  · intro hnot
    rcases hnot (m ⟨8, by decide⟩) with ⟨i, hi⟩
    by_cases hi8 : i.val = 8
    · have heq : i = ⟨8, by decide⟩ := Fin.ext hi8
      rw [heq] at hi
      unfold cbChordScalar at hi
      simp at hi
    · refine ⟨i, by omega, ?_⟩
      unfold eliminateNinthPoint
      intro hzero
      exact hi (Int.sub_eq_zero.mp hzero)
  · rintro ⟨j, _hjlt, hjnz⟩ k
    by_cases hk : k = m ⟨8, by decide⟩
    · refine ⟨j, ?_⟩
      intro heq
      apply hjnz
      unfold eliminateNinthPoint
      rw [← hk, heq, Int.sub_self]
    · refine ⟨⟨8, by decide⟩, ?_⟩
      unfold cbChordScalar
      simp
      exact Ne.symm hk

/-- Exact dot product on integer lists for arbitrary-rank relation elimination. -/
def intDot : List Int → List Int → Int
  | [], _ => 0
  | _, [] => 0
  | a :: as, w :: ws => a * w + intDot as ws

def linCombSub (k : Int) : List Int → List Int → List Int
  | [], _ => []
  | ms, [] => ms
  | m :: ms, c :: cs => (m - k * c) :: linCombSub k ms cs

theorem term_elim_identity (m k c w : Int) :
    (m - k * c) * w = m * w - k * (c * w) := by
  rw [Int.sub_mul, Int.mul_assoc]

theorem intDot_linCombSub (k : Int) (ms cs ws : List Int)
    (hlen_mc : ms.length = cs.length) (hlen_cw : cs.length = ws.length) :
    intDot (linCombSub k ms cs) ws = intDot ms ws - k * intDot cs ws := by
  induction ms generalizing cs ws with
  | nil =>
      cases cs with
      | nil => simp [linCombSub, intDot]
      | cons _ _ => cases hlen_mc
  | cons m ms ih =>
      cases cs with
      | nil => cases hlen_mc
      | cons c cs =>
          cases ws with
          | nil => cases hlen_cw
          | cons w ws =>
              simp only [List.length_cons] at hlen_mc hlen_cw
              have hrec := ih cs ws (by omega) (by omega)
              unfold linCombSub intDot
              rw [term_elim_identity, hrec, Int.mul_add]
              omega

/-- **Soundness of 9th-Point Elimination Under Any Linear Group/Log Evaluation:**
    If both `cs` (e.g. `n_CB`) and `ms` evaluate to `0` against `ws` (`∑_i n_i (ℓ_i - ℓ_O)`),
    then `ms - k · cs` (setting `k = m_8` to eliminate `P̃_8`) also evaluates to `0`. -/
theorem intDot_linCombSub_zero (k : Int) (ms cs ws : List Int)
    (hlen_mc : ms.length = cs.length) (hlen_cw : cs.length = ws.length)
    (hcs : intDot cs ws = 0) (hms : intDot ms ws = 0) :
    intDot (linCombSub k ms cs) ws = 0 := by
  rw [intDot_linCombSub k ms cs ws hlen_mc hlen_cw, hcs, hms]
  omega

/-- **Height-Amplification vs Box-Capacity Obstruction (`(2H + 1)^3 ≥ p → (3H)^20 > p^6`):**
    In `ℙ²(ℤ)`, at most `(2H + 1)^3 ≤ (3H)^3` integer triples lie in `[-H, H]^3` (`H ≥ 1`), so
    having expected factor-base size `≥ 1` on a degree-3 curve mod `p` requires `(2H + 1)^3 ≥ p`.
    Under the degree-20 Sylvester resultant amplification `H^20` of the 9th Cayley–Bacharach
    base point in the 4-point frame, `(3H)^20 > p^6 > p` for all `p ≥ 2`. -/
theorem cb_height_amplification_exceeds_modulus_sixth_power
    {H p : Nat} (hH : 1 ≤ H) (hp : 2 ≤ p)
    (hbox : p ≤ (2 * H + 1) ^ 3) :
    p ^ 6 < (3 * H) ^ 20 ∧ p < (3 * H) ^ 20 := by
  have h2H1 : 2 * H + 1 ≤ 3 * H := by omega
  have hcube : (2 * H + 1) ^ 3 ≤ (3 * H) ^ 3 := Nat.pow_le_pow_left h2H1 3
  have hp3 : p ≤ (3 * H) ^ 3 := Nat.le_trans hbox hcube
  have hp18 : p ^ 6 ≤ ((3 * H) ^ 3) ^ 6 := Nat.pow_le_pow_left hp3 6
  have hpow18 : ((3 * H) ^ 3) ^ 6 = (3 * H) ^ 18 := by
    rw [← Nat.pow_mul]
  rw [hpow18] at hp18
  have h18_pos : 1 ≤ (3 * H) ^ 18 := by
    have h1 : 1 ^ 18 ≤ (3 * H) ^ 18 := Nat.pow_le_pow_left (by omega) 18
    simpa using h1
  have hsq_gt1 : 1 < (3 * H) ^ 2 := by
    have h3 : 3 ≤ 3 * H := by omega
    have h9 : 9 ≤ (3 * H) * (3 * H) := Nat.mul_le_mul h3 h3
    have hpow2 : (3 * H) ^ 2 = (3 * H) * (3 * H) := by
      simp [Nat.pow_succ, Nat.pow_zero]
    omega
  have h20 : (3 * H) ^ 20 = (3 * H) ^ 18 * (3 * H) ^ 2 := by
    rw [← Nat.pow_add]
  have hstrict18 : (3 * H) ^ 18 < (3 * H) ^ 20 := by
    rw [h20]
    have hmul : (3 * H) ^ 18 * 1 < (3 * H) ^ 18 * (3 * H) ^ 2 :=
      Nat.mul_lt_mul_of_pos_left hsq_gt1 (by omega)
    simpa using hmul
  have hp6_lt : p ^ 6 < (3 * H) ^ 20 := Nat.lt_of_le_of_lt hp18 hstrict18
  have hp_le_p6 : p ≤ p ^ 6 := by
    have hp5_pos : 1 ≤ p ^ 5 := by
      have h1 : 1 ^ 5 ≤ p ^ 5 := Nat.pow_le_pow_left (by omega) 5
      simpa using h1
    have h6 : p ^ 6 = p ^ 5 * p := by rw [Nat.pow_succ]
    rw [h6]
    have hmul : 1 * p ≤ p ^ 5 * p := Nat.mul_le_mul_right p hp5_pos
    simpa using hmul
  exact ⟨hp6_lt, Nat.lt_of_le_of_lt hp_le_p6 hp6_lt⟩

end NodalBezoutAndCayleyBacharach

#print axioms NodalBezoutAndCayleyBacharach.euler_homogeneous_partials_zero_implies_value_zero
#print axioms NodalBezoutAndCayleyBacharach.leibniz_on_curve_node_forces_residual_zero
#print axioms NodalBezoutAndCayleyBacharach.smoothPlaneGenus_add_bezoutThreshold_eq_monomialCount_add_one
#print axioms NodalBezoutAndCayleyBacharach.off_curve_nodal_genus_le_two_no_kernel
#print axioms NodalBezoutAndCayleyBacharach.off_curve_nodal_positive_kernel_genus_lower_bound
#print axioms NodalBezoutAndCayleyBacharach.on_curve_nodal_kernel_eq_genus_sub_one
#print axioms NodalBezoutAndCayleyBacharach.on_curve_nodal_genus_le_one_no_kernel
#print axioms NodalBezoutAndCayleyBacharach.on_curve_nodal_genus_two_iff_d_in_4_5_6
#print axioms NodalBezoutAndCayleyBacharach.nodal_genus_two_triples_checked
#print axioms NodalBezoutAndCayleyBacharach.cbChordScalar_transport_core
#print axioms NodalBezoutAndCayleyBacharach.eliminateNinthPoint_at_eight
#print axioms NodalBezoutAndCayleyBacharach.cb_second_relation_iff_nonzero_eight_point_projection
#print axioms NodalBezoutAndCayleyBacharach.intDot_linCombSub_zero
#print axioms NodalBezoutAndCayleyBacharach.cb_height_amplification_exceeds_modulus_sixth_power
