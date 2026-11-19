# Prospective protocol: JKSST projective-frame Xedni panel with collinearity separation

Date: 2026-11-18

Status: prospectively specified and wired to `scripts/checkpoint.sh gate`; no
fresh natural-lift row has been generated because no S3 checkpoint upload
token or authorized AWS profile is present in this environment. [pcc:unverified]

## Question

When four selected finite-field points are normalized by `PGL_3(F_p)` to the
standard projective frame `(1:0:0), (0:1:0), (0:0:1), (1:1:1)`, the remaining
`r - 4` points are lifted via 3D LLL (`O(p^(2/3))` coordinates), the plane
cubic is optimized on the homogeneous projective-congruence sublattice, and
curve-independent pre-lift collinear triples (`det([P_a, P_b, P_c]) = 0`) are
explicitly separated from cubic-dependent relations, what is the non-collinear
exact relation rate for `r` in `{6, 7, 8, 9}` across `p` in
`{31, 67, 127, 251, 509}`? [pcc:unverified]

## Motivation from the November 17 forensic audit

Post-hoc algebraic-geometric decomposition (`audit_nov17_panel.py`,
`PANEL_DECOMPOSITION.json`) of the immutable 1,600-row November 17 panel
(`research/xedni_plane_group_20261117/run/rows.jsonl`) established two facts
that reshape the next experiment [pcc:unverified]:

1. **Chord-origin collinearity aliasing**: 66 of 67 certified relations overall
   — and 58 of 58 (100.0%) across `r = 7, 8, 9` — transport to fixed-flex
   vectors `r = +-(e_a + e_b + e_c)` with `det([P_a, P_b, P_c]) = 0` over `Z`.
   By Bezout's theorem (`P_a + P_b + P_c ~ H ~ P_u + P_v + O`), those 58
   relations hold on every smooth cubic through the lifted points and do not
   test Mordell--Weil dependence of the optimized cubic. [pcc:unverified]
2. **Naive `Z = 1` height explosion**: lifting all 9 points with `Z_i = 1` and
   imposing affine congruence `c = 1 * c_source (mod p)` produces `r = 9`
   cubics with `~ 18.6 log_2(p)` coefficient bits (`105.5` median bits at
   `p = 251`; `521` bits on the 28-bit control), whereas JKSST Steps 3--9
   (`ca-icx xedni-lift --model jksst-plane-cubic`) lowers `r = 9` cubic
   coefficients to `~ 8.0 log_2(p)` bits (`29` bits at `p = 251`; `223` bits
   at 28-bit `p`). [pcc:unverified]

## Primary estimands and falsification rule

1. **Primary estimand**: `cubic_dependent_success / eligible` (certified exact
   lifted relations whose fixed-flex transport is **not** a pre-lift `Z^2`
   collinear triple), alongside `dl_recovered / eligible` under
   non-collinear-first, invertible-target-first candidate ordering.
   [pcc:unverified]
2. **Secondary diagnostic**: `collinear_alias / eligible` (tracked separately
   and excluded from the cubic-dependence claim because under `PGL_3(F_p)` +
   3D-LLL any `F_p`-collinear triple sharing two frame vertices lifts to a
   coordinate/diagonal integer line with `O(p^(1/2))` norm, which remains an
   `O(r^3 / p)` finite-field triple coincidence). [pcc:unverified]
3. **Prediction and decision boundary**:
   - Even after cutting `r = 9` cubic height from `~ 18.6 log_2(p)` to
     `~ 8.0 log_2(p)` bits, canonical heights on generic non-planted lifts grow
     with `log p`, so `cubic_dependent_success / eligible` is predicted to fall
     at least as fast as `O(1/p)` across `p >= 127`. [pcc:unverified]
   - **Survive (stage lead)**: `p * (cubic_dependent_success / eligible)` grows
     monotonically or stays bounded away from zero across `p = 127, 251, 509`
     with zero certificate failures. [pcc:unverified]
   - **Kill / bounded null**: zero `cubic_dependent_success` rows at `p >= 251`
     or `p`-scaled decay consistent with `O(1/p)`. [pcc:unverified]

## Controls and gate

- `python3 research/xedni_chord_bridge_and_frame_20261118/paired_jksst_runner.py selftest`
  must pass before any run. [pcc:unverified]
- `paired_jksst_runner.py run` invokes `scripts/checkpoint.sh gate` before row
  zero and aborts nonzero if `.resume/RESUME.md` is incomplete or S3 upload is
  unavailable (tracked in
  `problems/xedni-full-rank-checkpoint-access.md`). [pcc:unverified]

## Frozen command (to run only after `scripts/checkpoint.sh gate` passes)

```sh
timeout 3600 python3 research/xedni_chord_bridge_and_frame_20261118/paired_jksst_runner.py run \
  --binary suite/target/release/ca-icx \
  --output research/xedni_chord_bridge_and_frame_20261118/run/rows.jsonl \
  --master xedni-jksst-noncollinear-20261118-v1 \
  --primes 31,67,127,251,509 --families generic,j0 \
  --r-values 6,7,8,9 --trials 25
```
