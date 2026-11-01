---
title: "Cubic five-gluing: exact source census and proof checks"
date: 2026-10-25
geometry: margin=0.85in
fontsize: 10pt
---

The Rust extension identifies **252 exact binary source models**, grouped
into **126 quadratic-twist pairs**, that pass the five-torsion criterion
and fail the earlier three-torsion criterion over F512/F8. All 126 pairs
also pass the small-geometric-isogeny exclusions. The written proof gives
a genus-three Jacobian isogeny for at least one source twist in each pair.
**A novel affected family and an explicit log transfer are not established.**

This continues the user's search for a novel criterion and proof. Beating
rho is not a gate. The experiment code is Rust in cryptanalysis; Python
is used only for command receipts and document/figure rendering.

## Exact results

| Check | Observed result | Scope |
|---|---:|---|
| Weighted Lagrangians at ell=5 | 19,656 per form | all four nonzero q residues |
| Transverse Lagrangians | 17,280 per form | coordinate intersections zero |
| GL2(F5) matrices checked | 480 | all compatible q, using det M=q cubed |
| Positive matrices | 184 | 180 split-distinct, four scalar |
| Criterion/enumeration disagreements | 0 | independent RREF subspace enumeration |
| Positive ell=11 constructions | 5,950 | constructive checks; negative cases not enumerated |
| Full-absolute-degree source models | 1,008 | a=0,1 and all 504 full-degree b in F512 |
| Five-positive, three-negative source models | 252 | complete exact model census |
| Small-isogeny screen | 126/126 twist pairs pass | degree 1 through 6 excluded geometrically |
| Rust release tests | 39 pass | all targets, including existing sweeper tests |
| Lean fixed certificate | five declarations pass | general classification and geometry unformalized |
| Transitive Lean audit | eight theorems, zero failures | includes three generated structure theorems; no native trust |

The 1,008 sources divide equally into four groups: both torsion screens
positive, only three positive, only five positive, and both negative:
252 models in each. These are exact finite counts, not sampled yields.
The five-only models have traces
$\pm7,\pm13,\pm17,\pm23,\pm37,\pm43$.
They represent 14 absolute Frobenius orbits of coefficients, not 252
unrelated families. All field arithmetic comparisons agree between the
log-table and raw polynomial paths. Screening/counting logic is shared;
there is no external independent implementation review.

![Exact counts by source trace. All displayed models pass the geometric screen; the existence theorem selects one unknown twist per pair. No performance or large-field yield is inferred.](cubic-gluing-figures/source-traces.pdf){width=95%}

## One concrete twist pair

Use $K=\mathbb F_2[z]/(z^9+z+1)$, encoded by modulus 515, and
$E_a:y^2+xy=x^3+a x^2+48$ with a=0 or 1. In this basis
$j=350$, $j^8=70$.

| Model | Exact source order | Trace | Prime factors |
|---|---:|---:|---|
| a=0, b=48 | 520 | -7 | 2 cubed times 5 times 13 |
| a=1, b=48 | 506 | 7 | 2 times 11 times 23 |

The modular values, in order
$\Phi_3(j,j^8),\Phi_5(j,j^8),\Phi_3(j^2,j^8),\Phi_3(j,(j^8)^2)$,
are **24, 306, 398, 201**. All are nonzero, and the Frobenius-distance
tests exclude degrees 1,2,4. Thus the sufficient geometric criterion holds.
It gives existence for one twist, preserving its prime subgroups away
from five. It does not select that twist or supply target coordinates.
No generator was selected, so the EC1 subgroup identity remains null.

The illustrative canonical module matrix $M=\operatorname{diag}(3,4)$,
$q=3$ modulo five, has basis vectors
$(1,0,3,0,4,0)$, $(0,4,0,4,0,0)$, $(0,1,0,0,0,4)$.
The Lean certificate checks independence, Frobenius stability, pairwise
basis isotropy and coordinate transversality for exactly this module.
It does not instantiate these vectors as points on $E[5]$.

## Proof and novelty status

The proof chain is [the module theorem](CUBIC_GLUING.md), then
[the indecomposability lemma and binary criterion](FIVE_GLUING_GEOMETRY.md).
Both are derived written proofs. The fixed finite module is checked in
Lean 4.34.1, commit 5045d0056413266e57c625dcd7c365b10e377c52,
with no external packages. Each of the five named declarations depends
only on propext. The transitive audit also covers the generated theorems.
The [proof map](formal/README.md) states the missing general and geometric bridges.

Tian's isotropic-quotient approach is published prior work; Hess's
generalized descent already gives broad existence for these binary sources.
The inspected Tian 2020 preprint assumes a suitable kernel rather than
stating this exact classification. This is not a novelty certification:
the full 2023 journal article remains unread, and absence in web searches
does not establish priority. The 2018 cofactor-two abstract describes an
odd-characteristic construction. These sources do not justify a claim that
our exact binary criterion is new. No weak-curve catalogue entry or
verified isogeny-route edge has been added.

## Reproduction and retained evidence

From the repository root, with the pinned Rust environment:

```sh
cargo run --release --locked --manifest-path experiments/ghs-sweeper/Cargo.toml \
  --example cubic_gluing -- exhaustive
cargo run --release --locked --manifest-path experiments/ghs-sweeper/Cargo.toml \
  --example cubic_gluing -- binary-census
cargo run --release --locked --manifest-path experiments/ghs-sweeper/Cargo.toml \
  --example five_gluing_geometry
```

For Lean, run `lake build` in `formal/`. The repository corpus gate also
builds and audits it alongside all previously covered sources.

The module/census contract and Rust source were frozen at `0c803777`;
the partial Lean project at `78bda02c`; the geometric check and proof at
`b71fec1c`. `cubic-gluing-checks/census-commands.json` and
`geometry-commands.json` retain exact argument arrays, source and output
digests, exits, revisions and execution durations. Durations are receipts,
not comparable performance measurements. Large JSON output is stored as
lossless deterministic gzip, with both stored and uncompressed hashes.

Formatting and Clippy with warnings denied passed. All 39 release tests
passed after adding the geometry checks. The old 32-file Hess, 30-file
three-gluing and 63-file kernel manifests remain separate frozen evidence.
The core sweeper, dependencies and checkpoint fingerprints are unchanged.
The 355 older denominator jobs were not resumed by these separate checks.
The artifact policy explicitly retains the three pre-existing frozen report
PDFs (78--94 kB each), preserving their manifest bytes during integration onto
main. New reports and compressed outputs fit the normal size thresholds.

The first full Lean-corpus replay failed because this sparse checkout
lacked the tracked `src/curve.c` needed by an existing GLV source-binding
check. A second replay exposed a stale pre-existing live-source pin: main's
later C changes altered the whole-file hash while preserving the exact table
selector and guards. Both failures are retained. The new gate preserves the
old receipt, replays its historical source and both negative controls, then
checks the current main source separately with the same selector assertions
and negative controls. No C code or historical GLV artifact was changed.
The third replay passes for all 95 research Lean sources; the new dated
corpus receipt binds the current and historical source hashes separately.

The older scope, kernel and criterion figures were checked and retain
their original scope. New diagrams show the five-gluing hypotheses and
unfinished reconstruction. Canonical curve/isogeny graphs remain unchanged.

## Remaining work against the request

| Requirement | Status |
|---|---|
| New recognition criterion with written proof | Derived and exactly checked in the stated finite cases; publication priority unresolved |
| Rust sweeper extension in crypto/cryptanalysis | Implemented and locally verified |
| Novel affected curve family | Not established |
| Full Lean proof | Partial fixed case only |
| Explicit selected genus-three target and subgroup/log transfer | Not constructed or performed |
| Construction, transfer and solver costs | Not measured; not replaced by the short check runtimes |

The next construction target is the b=48 twist pair. It requires actual
five-torsion coordinates, a characteristic-two quotient reconstruction,
arithmetic twist selection and an evaluated prime-subgroup isogeny. The
specific exit conditions remain in the
[problem record](../../problems/binary-cubic-gluing-target-and-novelty.md).
