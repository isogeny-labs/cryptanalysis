#set page(paper: "a4", margin: 1.6cm)
#set text(size: 9pt)
#show raw: set text(size: 8pt)
#let horizontalrule = line(length: 100%)
= Representation technique in `ic bench` (Delaplace–May 2019 / DFKM
2020)
<representation-technique-in-ic-bench-delaplacemay-2019-dfkm-2020>
2026-11-20. Owner request: "can we do this for our ic", answered with
all three variants (a), (b), (c). PR: cryptanalysis \#1877; trunk
tracking PR isogeny-labs/workspace\#38. Every number here is
`[pcc:unverified]` (no pcc claim minted); every logarithm in every row
below was recovered and verified by `ic bench`.

== Source
<source>
Delaplace, May, #emph[Can we beat the square root bound for ECDLP over
F\_{p^2} via representations?], NuTMiC 2019, ePrint 2019/800 (talk
slides `nutmic2019.imj-prg.fr/slides/Delaplace_Nutmic.pdf`; the host,
ePrint and the CASA mirror were all blocked by this session’s network
policy, so the paper was not re-read here; its content is taken from
crypto’s `research/representation_join_20261021/README.md`, which read
the DFKM 2020 follow-up, hal-02427655). Mechanism: write `k` as a sum,
join pairs of lists, keep only partial sums whose abscissa lies in a
structured subset (the subfield `F_p`); many representations of one
solution survive the filter. The algorithmic content is the step that
#emph[lists only] the filtered partial sums (summation polynomial + fast
multipoint evaluation), not the filter.

Prior work in the lab: crypto `research/representation_join_20261021`
(bounded C++ reference of DFKM, no timings),
`research/lead_sweep_20261110/LEAD-ICP-representation-subset-sum` (timed
out, no data), `research/representation_leads_20261109` (binary
representation derivations). research-kb was unreachable from this
session.

== What was built (all in `suite/`)
<what-was-built-all-in-suite>
#align(center)[#table(
  columns: 3,
  align: (col, row) => (left,left,left,).at(col),
  inset: 6pt,
  [lead], [code], [what it is],
  [(a)],
  [`descent-algebraic:m=4,inter_dim=l'`
  (`pq_descent_symbolic::descend_split4`, `ic_framework/plugins.rs`)],
  [balanced split `S3(x1,x2,u)`, `S3(x3,x4,w)`, `S3(u,w,xR)` with `u, w`
  in `span(1, z, …, z^(l'-1))`; `l' = n` is the plain chained `S5`
  descent. `3n` equations in `4n'+2l'` unknowns, at most cubic. Unit
  test checks every descended equation against the `S3` word formula bit
  for bit.],
  [(b)],
  [`rep-join:m=..,filter_bits=d` (`ic_framework/rep_join.rs`)],
  [generic signed `m`-list meet in the middle, `m = 2..9`, pair sums and
  probes kept only when the abscissa hash lies in a `2^-d` subset.
  `d = 0` is plain MITM at `m`.],
  [(c)],
  [`--fp2-bits`, `fp2-subfield`, `fp2-weil` (`ic_fp2.rs`,
  `cli/tools/ic/bench.rs`)],
  [curves over `F_{p^2}` with `a, b` not both in `F_p` (order by BSGS on
  three points), the subfield abscissa base, and Gaudry’s `n = 2`
  decomposition (Weil restriction of `S3`, a quartic in `e1 = x1+x2`
  over `F_p`, roots by `gcd(g, X^p - X)` + Cantor–Zassenhaus). Generic
  oracles run on it unchanged.],
)
]

== Preregistered predictions (counting argument, stated before any run)
<preregistered-predictions-counting-argument-stated-before-any-run>
- #block[
  #set enum(numbering: "(a)", start: 2)
  + generic: the `(m-2)`-tuple search is exhaustive, so the filter saves
    memory and lookups, never additions. Once the `m`-sums cover the
    group, cost per relation is about `N / |pair table|` for every `m`
    (the `m = 2` cost); below that, worse by up to `C(m,2)`. The filter
    multiplies additions by about `2^d`. #strong[No `m` beats the
    baseline.]
  ]

- #block[
  #set enum(numbering: "(a)", start: 1)
  + restricting the intermediates to `l'` bits is the hybrid approach on
    the intermediates: `log2(expected solutions) = 4n' + 2l' - 3n`
    either way, so it trades solutions for unknowns and should not beat
    the `m = 2, 3` descents per relation.
  ]

- #block[
  #set enum(numbering: "(a)", start: 3)
  + the subfield base works; the algebraic oracle (`fp2-weil`) is the
    only arm that can beat table MITM, and its distance to rho should
    not shrink (Gaudry `n = 2` is `~q` overall against rho’s `q^{1/2}`).
  ]

== Results
<results>
=== (b) lead sweep, trunk protocol, phase 1 (registry e840213ad5cf)
<b-lead-sweep-trunk-protocol-phase-1-registry-e840213ad5cf>
Both leads #strong[FAIL] phase 1 (no `m` beats the registry baseline on
every instance). Speed-up \= baseline S / lead S, paired geomean, 95%
bootstrap.

#align(center)[#table(
  columns: 5,
  align: (col, row) => (left,right,right,right,right,).at(col),
  inset: 6pt,
  [instance], [`d=0`, m\=2], [`d=0`, best m≥3], [`d=2`, m\=2], [`d=2`,
  best m≥3],
  [prime-16],
  [1.000],
  [0.825 (m\=3)],
  [0.740],
  [0.584],
  [prime-18],
  [1.000],
  [0.759 (m\=3,4)],
  [0.789],
  [0.546],
  [char2-17],
  [1.000],
  [0.492 (m\=8)],
  [0.483],
  [0.296],
  [char2-21],
  [1.000],
  [0.262 (m\=3)],
  [0.407],
  [0.149],
  [koblitz-23],
  [0.023],
  [0.023],
  [0.023],
  [0.023],
)
]

`m = 2, d = 0` reproduces the baseline to the operation (A/A control of
the plug-in). Koblitz: the baseline is `mitm-frobenius` (table folded by
the signed Frobenius); `rep-join` builds the full table, which dominates
S there. Full tables: `runs/LEAD-rep-join-*/*/SUMMARY.md`.

=== (c) `fp2` panel (direct `ic bench`, outside the lead-sweep registry)
<c-fp2-panel-direct-ic-bench-outside-the-lead-sweep-registry>
The registry has no `fp2` regime (adding one needs its own trunk PR), so
this is a paired panel: same seed, instance and planted targets per arm,
6 repeats, matched rho (negation walk). Speed-up \= `mitm` S / arm S.

#align(center)[#table(
  columns: 7,
  align: (col, row) => (right,right,right,right,right,right,right,).at(col),
  inset: 6pt,
  [k], [rho S], [`mitm` S/rho], [`fp2-weil` speed-up \[95%\]],
  [`fp2-weil` S/rho], [`rep-join` m\=3 / m\=4], [`rep-join` m\=3, d\=4],
  [16],
  [1.79],
  [90],
  [6.98 \[6.28, 7.83\]],
  [13.0],
  [1.00 / 0.99],
  [0.90],
  [20],
  [1.53],
  [749],
  [35.2 \[27.9, 44.5\]],
  [22.2],
  [1.00 / 1.00],
  [0.97],
  [24],
  [1.46],
  [4251],
  [128 \[110, 150\]],
  [33.9],
  [1.00 / 1.00],
  [0.99],
  [28],
  [1.22],
  [16893],
  [284 \[250, 341\]],
  [60.5],
  [1.00 / 1.00],
  [1.00],
)
]

The default base is every `F_p` abscissa (about `p/2`), so the table
arms pay about `q/8` additions to build the pair table, which swamps
everything else: `mitm` is a deliberately weak yardstick here and
`rep-join` ties it. Priced units of this regime are measured on the host
(no pinned ratios exist for `fp2`): an exploratory run of the same panel
under lighter load gave `fp2-weil` 427x / S/rho 40 at k \= 28, so
absolute `fp2-weil` S carries about 1.5x run-to-run noise; the ordering
does not change.

=== (a) split descent, `l'` sweep
<a-split-descent-l-sweep>
char2 `n = 17`, `binary-subspace` dimension `n' = 6`, `ic bench` default
seed, 30 targets per cell, `sat-cdcl` with a 200,000-conflict / 30 s
budget per system. Deterministic: the recorded rerun reproduced the
exploratory sweep conflict for conflict. Expected solutions per target
(ordered, twist included) `2^(4n' + 2l' - 3n) = 2^(2l' - 27)`.

#align(center)[#table(
  columns: 6,
  align: (col, row) => (left,right,right,right,right,right,).at(col),
  inset: 6pt,
  [arm], [unknowns], [equations], [relations / 30], [over budget],
  [solver s / target],
  [m \= 2 descent (control)],
  [12],
  [17],
  [1],
  [0],
  [0.03],
  [m \= 3 descent (control)],
  [18],
  [17],
  [cell killed at the 2,400 s wall (resource limit, not a result)],
  [],
  [],
  [m \= 4, l’ \= 4],
  [32],
  [51],
  [0],
  [0],
  [0.00],
  [m \= 4, l’ \= 6],
  [36],
  [51],
  [0],
  [0],
  [0.04],
  [m \= 4, l’ \= 8],
  [40],
  [51],
  [0],
  [0],
  [0.72],
  [m \= 4, l’ \= 10],
  [44],
  [51],
  [1],
  [23],
  [14.5],
  [m \= 4, l’ \= 11],
  [46],
  [51],
  [0],
  [30],
  [18.9],
  [m \= 4, l’ \= 12],
  [48],
  [51],
  [0],
  [30],
  [21.0],
  [m \= 4, l’ \= 13],
  [50],
  [51],
  [0],
  [30],
  [24.0],
  [m \= 4, l’ \= 17 \= n (unrestricted chain)],
  [58],
  [51],
  [exploratory, 4 targets: 4/4 over budget (sat-cdcl); f4-f2 \> 400 s
  for 4 targets],
  [],
  [],
)
]

Below `l' = 10` the restriction leaves almost no solutions (`2^-11` per
target at `l' = 8`) and the solver proves that quickly; from `l' = 11`
up the systems that do have solutions are out of the solver’s reach. The
one productive cell, `l' = 10`, cost about 440 solver-seconds per
relation, against about 0.9 s for the `m = 2` descent on the same base
(and the descents themselves are about `10^4` times dearer than the
`mitm` table at this size: exploratory 2-repeat run,
`descent-algebraic:m=2` S \= 1.4e6 against `mitm` S \= 33). As
predicted, the restriction trades solutions for unknowns; it never
produced a cheaper relation.

== Reading
<reading>
+ #strong[The filter is not the algorithm.] Generically (b), keeping
  only partial sums in a structured subset cannot reduce work: every
  tuple is still enumerated. The measured filter costs are `0.5x–0.8x`
  against the unfiltered join, the direction predicted.
+ #strong[The algebra is the algorithm.] On the one regime where the
  paper’s filter exists (c), listing only the subfield decompositions
  algebraically (`fp2-weil`) beats table MITM by `7x–284x`, growing with
  `k`. But its gap to rho also grows (`13 → 61`): Gaudry `n = 2` with a
  `p/2` base needs about `p` relations and a linear-algebra step of
  about `p^2 = q`. Nothing here approaches rho.
+ #strong[In the binary Weil-descent setting (a)], restricting the
  intermediates is hybrid guessing on them. It moves work between
  solution count and system size; it did not lower the cost per
  relation.

== Reproduce
<reproduce>
```
# build (any checkout of this branch)
(cd suite && cargo build --release --bin ca-ic)
# (b): trunk runner, phase 1
python3 <workspace>/tools/lead_sweep.py run research/representation_join_ic_20261120/leads/rep-join-generic.json --phase auto --cryptanalysis . --out-root research/representation_join_ic_20261120/runs
python3 <workspace>/tools/lead_sweep.py run research/representation_join_ic_20261120/leads/rep-join-filtered.json --phase auto --cryptanalysis . --out-root research/representation_join_ic_20261120/runs
# (c)
research/representation_join_ic_20261120/fp2_panel.sh suite/target/release/ca-ic research/representation_join_ic_20261120/runs/fp2-panel
# (a)
research/representation_join_ic_20261120/split_descent_sweep.sh suite/target/release/ca-ic research/representation_join_ic_20261120/runs/split-descent 30
```

Host: 4 vCPU / 15 GiB cloud container, no hardware PMU, shared; wall
times are not claims. Benchmark records:
`benchmarks/records/20261120T*-rep-join-*`,
`*-fp2-representation-panel`, `*-split-descent-m4-lprime`. Raw data is
in Git under `runs/` (S3 upload unavailable from this container: no
credentials).
