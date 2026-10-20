# Prospective D183/f6 signed floor-incidence holdout

The first frozen `D_K=-15` cell ended at an explicitly recorded class
reachability gate: `p=139` gave two CM `j` values but zero rational
`X_0(11)` starting points. The separately checked candidate scan gives
`(D_K/11)=-1` there. This second cell uses `D_K=-183`, for which 11 splits,
and tests the even-block sign pattern suggested by D39 after D87's
odd-block alignment. This parity rule remains a conjecture; the exact
local ratio criterion in `PROTOCOL.md` is independent of it.

Freeze Frobenius-order conductor `f=6`, Hecke degrees `[2,3]`, and
`PFS_WALK_PMIN=0`. The checked source should select `(p,|t|)=(1663,8)`,
with `8²-4·1663=-183·6²`. The ring-class numbers independently calculated
before this run are `h_1=8`, `h_2=8`, `h_3=24`, and `h_6=24`. Conditional
on two rational `X_0(11)` lifts per CM `j` and complete component
reachability, predict 128 columns in strata `(16,16,48,48)` at conductors
`1,2,3,6`, 64 degree-2 rows, 32 degree-3 rows, and combined full rank
`128-2h_6=80`.

The norm-2 class at conductor 3 has order 24. Predict two signed 24-row
degree-2 cycles with disjoint 24-column floor supports covering all 48
conductor-6 columns. The 16 degree-3 rows sourced at conductor 2 should
pair into eight equal-nonfloor-part pairs, each giving an exact signed
six-column floor vector; their supports should partition the floor.
The **prospective even-block hypothesis** predicts that each degree-2
cycle overlaps four pair blocks and has nonconstant signed ratios on at
least one of them. Hence the two cycle vectors should add two independent
floor directions beyond the eight pair differences. The subset
full/nonfloor rank forecasts are degree 2 `64/62`, degree 3 `32/24`, and
combined `80/70`, giving ten floor-supported directions. Preserve any
failed count, reachability, rank, pairing, or sign forecast verbatim.

`protocol_D183.json` freezes these predictions, the checked-Sage runtime,
the copied producer source and helper, and the prior scans before launch.
Use `/Volumes/SSD990/cryptanalysis/sage -python` with a 600-second cap,
retaining the process receipt and full matrix. Then independently verify
the 128 point conductor labels, 256 root counts with multiplicity against
both Hecke and classical modular polynomials, all group identities, exact
integer cycle/pair certificates, and `QQ` plus three modular ranks. These
are class-walk matrix diagnostics with `candidate_id: null`.
