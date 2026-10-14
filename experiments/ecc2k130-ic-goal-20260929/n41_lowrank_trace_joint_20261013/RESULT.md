# Target-conditioned trace cuts across two free pair-output families

Twelve selected trace projections of the public-target S3 equation can
reject an entire pair of unresolved output families before source masks or
signed points are chosen. On a frozen N41 W6 panel of 30 pseudorandom
public-point family pairs, sampled cross-rank-at-most-three cuts rejected
**15** family pairs, compared with **4** for the first twelve independent
ordinary trace projections. A deterministic row-kernel construction
produced twelve equation-independent cross-rank-one cuts and rejected
**8** pairs. The constructed positive family survived every variant, and
independent checked Sage replay reproduced four selected cases for each of
the two stronger variants. [Terminal verification](terminal.json) binds the
three exact panels, their source hashes, run caps, and both Sage audits.

## Joint equation and cut construction

The exact N41 field is `GF(2)[t]/(t^41+t³+1)` with curve
`EC1N41Ckb1h023d9a38bbf7`. This experiment uses the audited W6
**product-span relaxation** from the [bilinear family screen](../n41_bilinear_rank_screen_20261013/RESULT.md).
For fixed product labels `p,q`, the left and right reciprocal output
coordinates range over binary linear spaces with bases `u_i` and `v_j`.
The public raw-point reciprocal `t` appears in

`S3(c,d,t)=(tcd)²+tcd+c²+d²+t²`, with
`c=Σ αᵢuᵢ` and `d=Σ βⱼvⱼ`.

For a trace multiplier `λ`, the one-bit necessary equation is

`Tr(λt²) ⊕ Σᵢ αᵢ Tr(λuᵢ²) ⊕ Σⱼ βⱼ Tr(λvⱼ²)
 ⊕ Σᵢⱼ αᵢβⱼ Tr(λ((tuᵢvⱼ)²+tuᵢvⱼ)) = 0`.

Thus each trace cut is a Boolean bilinear form in two still-free
coordinates. The first variant samples multipliers until twelve linearly
independent values have cross matrices of rank at most three. Its comparator
takes the first twelve linearly independent multipliers from the same
deterministic stream. The row-kernel variant solves for multipliers that
annihilate all but one cross-matrix row; the informative revision discards
redundant **equations**, including cuts identically zero on the two-family
domain. No variant selects a source mask or a completed point before
applying its cuts.

The panel fixes a constructed positive product-family pair `(819,176)` at
reciprocal `1515824644274`, the same pair at the public-point reciprocal
`1000731834126`, and 30 product-family pairs drawn by the frozen seed
`202610131700`. The source spaces have six or seven binary dimensions.
The constructed positive has one exact S3 coordinate pair; every public
panel case has zero exact S3 pairs in this restricted family sample.

| Twelve-cut method | Whole-family rejections among 30 sampled public cases | 95% descriptive Wilson interval | Surviving coordinate pairs across those 30 cases | Parent wall / sampled peak combined RSS |
| --- | ---: | ---: | ---: | ---: |
| First independent trace multipliers | 4 | 5.3%–29.7% | 46 | shared comparator in each run |
| Randomly found cross rank ≤ 3 | **15** | 33.2%–66.8% | **24** | 0.774 s / 26,296,320 B |
| Forced cross rows, multiplier-independent | 2 | 1.8%–21.3% | 66 | 3.320 s / 26,279,936 B |
| Forced cross rows, equation-independent | **8** | 14.2%–44.4% | 36 | 3.386 s / 26,247,168 B |

The 30 sampled cases are paired across variants. The rank-three cuts alone
rejected 13 cases retained by the ordinary cuts; the ordinary cuts alone
rejected two. These are finite-panel algorithmic diagnostics on an
unisolated host, not an isolated timing comparison or a measured ordinary
relation rate. Rank-three multiplier selection took up to 31,856 trials
in a sampled public case. The public-point product-family panel is a
four-source W6 slice, while the campaign's unpinned eight-point N41 gate
uses a different W8 four-pair source. The W8 gate remains the next
relation-yield test.

The [first Sage audit](audit_result.json) rebuilt four N41 relaxed output
spaces independently and checked all 4,096 coordinate pairs per
six-by-six case for the rank-three and ordinary cuts. The
[informative-row Sage audit](audit_info_result.json) did the same for its
four selected cases. Both rechecked the cross ranks, exact S3 hit counts,
and every twelve-cut survivor count. The native worker also directly
checked sampled trace-cut evaluations against the full field equation for
the deterministic variant. All runs used one worker and a frozen
120-second/4-GiB cap; raw logs and checked Sage runtime are preserved.

## N131 source-bound transfer

For an 18-by-18 cross matrix over `GF(2^131)`, forcing seven complete
rows to zero imposes at most `7·18=126` homogeneous binary conditions on
131 trace-multiplier bits. Its solution space has dimension at least five,
and every resulting cross matrix has rank at most eleven. This gives a
direct construction of low-rank **necessary** cuts for a fixed pair of
product families. If a family has a different output dimension, the
general bound is `rank ≤ r−k` whenever `k·s < 131`, where `r,s` are the
left and right output dimensions. The [proof map](PROOF_MAP.md) separates
the checked row-elimination lemma from the finite-field and rank-nullity
bridges.

The literal W18 product span has `2^35` product families per slot. A
pairwise family sweep therefore has **`2^70 = 1,180,591,620,717,411,303,424`**
ordered pairs; 600 seconds would require at least
`1.968·10^18` pair visits per second before creating a trace cut, source
filtering, or group replay. This rejects that literal N131 implementation
under the one-worker envelope. The useful next algorithmic question is
whether row-kernel cuts can be formed for **sets of product families at
once**, so the public point rejects a joint family region before the
`2^70` pair expansion. A candidate must first preserve the frozen N41 W8
public relation and then pass a whole-search N131 source bound.

All three panel protocols, the two Sage audit protocols, sources, binaries,
logs, and receipts are under this directory. `candidate_id` remains
`null` because this is a point-decomposition filter component. The
[preflight record](preflight_failures.json) retains the first Python
environment failure and the superseded row-kernel compile error; neither
started a measured worker.
