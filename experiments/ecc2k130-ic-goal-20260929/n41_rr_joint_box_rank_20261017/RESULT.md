# Six-slot determinant boxes have a sharp affine-trace boundary on N41

**An exact public-target Riemann–Roch screen excludes all 32 sampled sign-only six-slot boxes, while 65 boxes with an additional root or source-code choice saturate the 41-bit determinant-value space.** Each sign box contains 64 valid source-state combinations and has difference rank 34. Its explicit coordinate-linear functional is one on every determinant value, certifying that all 64 combinations miss the target. In each of 32 root-and-sign boxes, 32 two-code boxes, and the witness-containing two-code box, a prefix of at most 50 values already has difference rank 41. That exact rank prevents one linear functional from certifying the entire box. The independently replayed ordinary witness survives.

## Source and predeclared boxes

The source is the frozen six-slot fixed-seed W8 input for `EC1N41Ckb1h7d5e80d3c4d0`, on `GF(2)[t]/(t^41+t³+1)` with curve `y²+xy=x³+1`. Slots rotate by `(0,6,12,18,24,30)`. Each has 160 signed states from 40 pair codes; the raw public target is `(2026560328086,1928332930914)`. The source SHA-256 is `7fc0362121ecc510d9ec9ea62a17c1efc878cd96fed7292246675c1951f006fb`.

The [frozen panel](panel.json) was generated with Python RNG seed `20261017` using only source validity and folded-column disjointness, before determinant evaluation. It contains 32 boxes of each kind:

- **Sign:** one code and one x root per slot, with the two point signs free; 64 assignments.
- **Root and sign:** one code per slot, with both roots and both signs free; 4,096 assignments.
- **Two code:** two column-disjoint codes per slot, one predeclared state per code; 64 assignments.

A separate two-code positive control contains the six state IDs `(12,122,116,47,128,34)` from the archived ordinary public relation and six source-valid alternatives. Every frozen box has twelve distinct folded columns for each assignment. The independent audit checks seven distinct x coordinates for every evaluated determinant chart.

## Exact target-conditioned predicate

For six selected source points and `−Q`, form the seven-row evaluation matrix of `1,x,y,x²,xy,x³,x²y` in `L(7O)`. A genuine relation makes its determinant `D` zero. The producer computes `D` through the 35-term Laplace expansion over the three y-bearing columns. For a box with first value `d₀`, let `V` be the binary span of all differences `D(s)+d₀`. If `d₀` is outside `V`, a binary-linear functional `L` can satisfy `L(d₀)=1` and `L(V)=0`; then every determinant in that box is nonzero. If a subset of differences already spans all 41 field bits, no such single functional exists for the full box, and evaluation may stop without enumerating the remaining assignments.

[AffineCertificate.lean](AffineCertificate.lean) proves the nonzero implication and the abstract full-span obstruction for an additive group and a binary-linear functional. Lean 4.34.1 built both theorems; `#print axioms` reports only `propext`. The concrete rank, chart, determinant and curve bridges are independently replayed, with their formalization boundary in [PROOF_MAP.md](PROOF_MAP.md).

| Box kind | Frozen boxes | Complete boxes with no-zero certificate | Boxes reaching rank 41 | Determinants evaluated | Values to rank 41, min / median / max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sign | 32 | **32** | 0 | 2,048 | —; each final rank 34 |
| Root and sign | 32 | 0 | **32** | 1,407 | 42 / 44 / 48 |
| Two code | 32 | 0 | **32** | 1,399 | 42 / 43 / 50 |
| Witness two code | 1 | 0 | **1** | 42 | 42 |

The worker completed all 97 boxes in **14.205 s**, with **21,495,808 B** self peak RSS, below its frozen 180 s and 4 GiB diagnostic boundaries. These are ordinary-host stage measurements. The first successful worker result is retained as `result_v1.json`; the second run captured raw stdout/stderr and has the same box classifications, rank, stop count and first value in every row. All full-rank rows stop after a sound obstruction to this one certificate family; they do not classify the unvisited assignments as target hits or misses.

## Independent replay and decision

The [independent auditor](audit_result.json) used a different field multiplication and Euclidean inverse, formed the full 7×7 determinant by Gaussian elimination, and replayed the ordinary six-point group sum for **all 4,896 evaluated assignments**. It matched every saved producer first value, rank, stop and classification. Exactly one evaluated assignment reached the target: the frozen positive control. The auditor solved and stored 32 explicit coordinate-linear masks; [terminal replay](terminal.json) checked each mask against every value of its 64-assignment sign box using the producer's separate Laplace formula. Both worker stderr and auditor stderr are empty. The auditor took **5.250 s** and peaked at **21,676,032 B** on the same ordinary host.

This experiment gives a source-bound failure criterion for the proposed *single affine trace* gate: even the smallest four-state or two-code-per-slot boxes sampled here saturate the field after about 44 values. The sign-only certificate remains useful as an exact leaf filter. The next constructive gate should preserve the low-degree source-code and root algebra across several slots and test a genuinely nonlinear target constraint on an unpinned N41 relation before N131 promotion. The 35-term Laplace split of the determinant into left and right three-row minors is a concrete algebraic basis for such a joint constraint. `candidate_id` remains null until the full IC pipeline is specified.
