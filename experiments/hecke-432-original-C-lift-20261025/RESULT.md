# The original X0(27) point and E output identify all 1,800 p=997 sources

The paired coordinate map from the 1,800 noncuspidal rational level-432
source records to their original \(X_0(27)\) point and projected
\(E:y^2=x^3+432\) point is injective on this complete p=997 census. The
experiment recovers 342 distinct original level-27 points indexed by source curve
and 27-isogeny path, then pairs each with its independently audited E
output. All 1,800 \((C,E)\) keys occur once. Adding the terminal
16-isogeny \(j\)-invariant leaves the count at 1,800 keys.

## Coordinate recovery and measurement

The [protocol](protocol.json) was fixed before producer evaluation. For each
source curve and cyclic 27-chain, `evaluate_sage.py` solves the normalized
27a1 coordinate bridge using the source and terminal quotient
\(j\)-invariants. It then filters the roots by both intermediate
\(j(3\tau)\) and \(j(9\tau)\). Exactly one point remains for every one of
the 342 paths. The 1,800 source records are joined by exact curve model,
source label, and indexed 16/27 paths to the E outputs from the prior p997
projection experiment.

| Key | Distinct keys | Multiplicity histogram | Maximum multiplicity |
| --- | ---: | ---: | ---: |
| Original C point and E output | 1,800 | 1: 1,800 | 1 |
| Original C point, E output, terminal-16 j | 1,800 | 1: 1,800 | 1 |

The original C projection alone has **342** image points: 234 have four
rational sources each and 108 have eight each. The E coordinate separates
all sources within those C fibers in this census.

No observed \((C,E)\) group exceeds the degree-24 B-map fiber cap. The
experiment therefore establishes a complete source identifier at this
prime, while the assignment of the correct member of each three-point
rational B preimage coset remains a separate calculation. In particular,
finite-set injectivity does not furnish a low-degree rational B formula;
the preceding bounded q-series screen gives that separate limit.

`result.json` retains every source key, original C point, E point, terminal
invariants, input hashes, and complete histograms. `audit.py` independently
recomputes source coverage and all four modular \(j\)-invariants from the
saved points over \(\mathbf F_{997}\), checks the C and E equations, and
rebuilds both histograms. Its [receipt](audit.json) reports
`PASS_INDEPENDENT_ORIGINAL_C_AUDIT`.

## Proof map and replay

| Result | Evidence and formalization |
| --- | --- |
| Unique C coordinate for each of 342 original 27 paths | Producer root enumeration filtered by exact intermediate invariants; independent audit checks all four j-values and the C equation. |
| 1,800 distinct paired C/E keys | All 1,800 result rows, exact join to the earlier independently audited E-image input, and independent regrouping in `audit.py`. |
| Injective paired map preserves source count in its image | `OriginalCImage.paired_image_card`, checked with pinned Lean and mathlib revisions. |

The Lean theorem exposes injectivity as a hypothesis. Formalizing the
concrete coordinate evaluator and 1,800-row distinctness certificate in
Lean remains open; the independent finite-field replay provides that
premise for this experiment.

Replay from the repository root with the checked Sage launcher:

```sh
./sage --runtime-info
./sage -python experiments/hecke-432-original-C-lift-20261025/evaluate_sage.py
python3 experiments/hecke-432-original-C-lift-20261025/audit.py
```

The next screen should use the observed paired-coordinate separation to
search higher-degree rational functions on the modular curve, with a
frozen q-series precision and a held-out coefficient range. A recovered
formula would still require exact rational reconstruction, a modular
function identity proof, and an independent evaluation on these p997
sources to resolve their B lifts.
