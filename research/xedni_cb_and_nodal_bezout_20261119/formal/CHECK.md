# Lean 4 Formalization Audit — `NodalBezoutAndCayleyBacharach.lean` [pcc:unverified]

- **Toolchain:** `leanprover/lean4:v4.36.0` (`formal/lean-toolchain`) [pcc:unverified]
- **Command:** `/Users/adamburan/.elan/toolchains/leanprover--lean4---v4.36.0/bin/lean research/xedni_cb_and_nodal_bezout_20261119/formal/NodalBezoutAndCayleyBacharach.lean` [pcc:unverified]
- **Status:** Exit code `0`, `14 / 14` declarations kernel-checked, `0` `sorryAx`, `0` custom axioms (`axioms.txt` uses only standard foundations `propext`, `Quot.sound`, `Classical.choice`, or zero axioms). [pcc:unverified]

## Proof Map [pcc:unverified]

| Mathematical Statement | Lean Declaration | Axioms |
|---|---|---|
| Euler homogeneous identity forces `C(Q) = 0` from `∂_X C = ∂_Y C = ∂_Z C = 0` (`d ≥ 1`) | `euler_homogeneous_partials_zero_implies_value_zero` | `propext, Quot.sound` |
| Leibniz rule on `C̄ = E · G`: on-curve node `Q ∈ E` (`∇E(Q) ≠ 0`) forces `G(Q) = 0` (`Q ∈ E ∩ G`) | `leibniz_on_curve_node_forces_residual_zero` | *(none)* |
| Universal smooth genus vs Bézout kernel identity `g_smooth(d) + (3d + 1) = N_d + 1` (`d ≥ 3`) | `smoothPlaneGenus_add_bezoutThreshold_eq_monomialCount_add_one` | `propext, Quot.sound` |
| Off-curve nodes (`I_{Q_k}(E, C̄) = 0`): `g_geom ≤ 2` gives `r + 3δ > N_d` (zero kernel for all `d ≥ 4`) | `off_curve_nodal_genus_le_two_no_kernel` | `propext, Quot.sound` |
| Off-curve nodes with `K_off ≥ 1` satisfy `3 g_geom ≥ d² - 3d + 4 ≥ 9` (`g_geom ≥ 3`, `Θ(d²)`) | `off_curve_nodal_positive_kernel_genus_lower_bound` | `propext, Classical.choice, Quot.sound` |
| On-curve nodes (`I_{Q_k}(E, C̄) ≥ 2`, `2δ + r = 3d + 1`): `N_d + 1 = (3δ + r) + g_geom` (`K_on = g_geom - 1`) | `on_curve_nodal_kernel_eq_genus_sub_one` | `propext, Quot.sound` |
| On-curve nodes at `g_geom ≤ 1` (`2δ + r ≥ 3d + 1`) give `3δ + r ≥ N_d` (`K_on = 0` for all `d ≥ 4`) | `on_curve_nodal_genus_le_one_no_kernel` | `propext, Quot.sound` |
| On-curve nodes at `g_geom = 2` admit `2δ + r ≥ 3d + 1` and `K_on ≥ 1` iff `d ∈ {4, 5, 6}` | `on_curve_nodal_genus_two_iff_d_in_4_5_6` | `propext, Quot.sound` |
| Exact `g_geom = 2` triples `(4, 1, 11)`, `(5, 4, 8)`, `(6, 8, 3)` (`δ + r ≤ 12`) & `d = 7` cutoff (`39 > 36`) | `nodal_genus_two_triples_checked` | *(none)* |
| Cayley–Bacharach chord-origin scalar `n_CB = (-2,-2,1,1,1,1,1,1,1)` transports to `(1,..,1)` | `cbChordScalar_transport_core` | `propext` |
| 9th-point elimination `m' = m - m_8 · n_CB` zeroes coordinate `8` | `eliminateNinthPoint_at_eight` | `propext` |
| `m ∉ ℤ · n_CB` iff `m'` is a nonzero `r = 8` vector supported on `0..7` | `cb_second_relation_iff_nonzero_eight_point_projection` | `propext, Quot.sound` |
| Linear discrete-log specialization vanishes on `m - k · n_CB` whenever it vanishes on `m` and `n_CB` | `intDot_linCombSub_zero` | `propext, Quot.sound` |
| Box-capacity bound `(2H + 1)^3 ≥ p` (`H ≥ 1, p ≥ 2`) forces `(3H)^20 > p^6 > p` (9th-point wraparound) | `cb_height_amplification_exceeds_modulus_sixth_power` | `propext, Quot.sound` |

## Re-verify 2026-11-20

- `lean` 4.34.1 on host re-checked `NodalBezoutAndCayleyBacharach.lean`: exit 0, 14/14 decls, 0 sorryAx [pcc:unverified].
