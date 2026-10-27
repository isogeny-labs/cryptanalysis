# Frozen four-conductor Fricke balance panel

After the `D=-2631, f=6` matrix gave equal Fricke `+/-` ranks, test the
already independently audited `D_K=-7` matrices at reached conductors
`42,70,150,210`, in that order. Their Hecke degree supports are
`{2,3,7}`, `{2,5,7}`, `{2,3,5}`, and `{2,3,5,7}`. Fix the four input
SHA-256 values in `panel.py` before running it. The prospective prediction
is equal plus/minus ranks `52/52`, `70/70`, `250/250`, and `392/392`,
respectively, half of the saved full rational ranks. Retain every mismatch.

For each saved point, compute `W(P)=T-P` with `T=(16:-61:1)` on the exact
`11a1/F_p` group. Record whether the saved class is closed under `W`,
whether every relation row transports to an existing row, the number of
fixed points, and all point and row orbit counts. If point or row closure
fails, record that status and leave eigenspace ranks null. For a closed
matrix, project each row to `r_i+r_W(i)` and `r_i-r_W(i)` using the lower
column index in every two-point orbit. Compute ranks over `QQ`, `F_23`,
and `F_1000000007`; record the sum versus the archived full rank and the
column nullities. The coordinate change is invertible over `QQ` by the
checked pair lemma in PR #1196. This panel tests exact saved matrices,
with no new wall-time comparison or IC candidate promotion.
