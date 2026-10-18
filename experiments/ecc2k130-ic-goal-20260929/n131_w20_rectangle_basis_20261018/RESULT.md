# Exact W20 source partitions and affine-direction search

An exact census of the frozen N131 W20 selected-pair source finds **89,734**
occupied cosets for the best coordinate two-bit subspace, and an XOR
autocorrelation search finds **89,346** for the best two-plane among 2,016
planes spanned by the top 64 directions. The latter produces
**7,982,707,716** ordered nonempty two-slot rectangles, a **1.568%** reduction
from the prior fixed low-bit partition's **8,109,903,025**. This selects a
slightly better source grouping for an exact target-conditioned router; it
does not reduce the **17,435,882,025** ordered source-code assignments that
the grouping covers.

## Frozen method and measured results

The input is the selected-pair table
[`support_w20.tsv`](../n131_w20_sevenpair_gate_20261010/support_w20.tsv),
SHA-256 `21f190a925c60044ba85b89dbcef39a71407b0c852de7c7ab88c95bed05e8944`.
It has 524,493 support rows. An admissible unordered pair has masks
`a < a XOR 898618`, both present and with different columns. Removing the
seed's pivot bit yields a unique 19-bit selector. There are **132,045** such
selectors, independently reconstructed by both audits.

For each coordinate subspace of dimension 2, 3, or 4, `census.cpp` counts
the occupied cosets and full occupancy histogram. It exhausts respectively
171, 969, and 3,876 bit subsets. `affine.cpp` uses an exact integer Walsh
transform to compute the overlap `|A ∩ (A XOR d)|` for every nonzero 19-bit
direction `d`, sorts by overlap, then counts occupied cosets of each of the
2,016 planes spanned by pairs of the top 64 directions. The top-64 plane
search is a declared heuristic; the line search and coordinate census are
exhaustive within their stated families.

| Partition per slot | Occupied cosets | Ordered nonempty rectangles | Search extent |
| --- | ---: | ---: | --- |
| Prior low coordinate bits `3` | 90,055 | 8,109,903,025 | Fixed control |
| Best coordinate two-bit mask `4098` | 89,734 | 8,052,190,756 | All 171 masks |
| Best tested affine plane, directions `505271`, `344399` | **89,346** | **7,982,707,716** | Top-64 pair search, 2,016 planes |
| Best coordinate three-bit mask `3080` | 58,909 | 3,470,270,281 | All 969 masks |
| Best coordinate four-bit mask `67842` | 32,389 | 1,049,047,321 | All 3,876 masks |

The best affine line direction is `214963`: its overlap is 34,162 and it
forms 114,964 occupied two-element cosets. The full line search spans
524,287 nonzero directions. The coordinate-width and affine searches use
different rectangle capacities; compare their counts only with the
corresponding per-rectangle work and memory.

The one-worker coordinate census completed in **5.959 s** at sampled
combined RSS **38,928,384 bytes**. The corrected affine search completed in
**2.681 s** at sampled combined RSS **45,481,984 bytes**. Both were capped at
180 s and 4 GiB and run through the checked repository Sage launcher.
These are source-precomputation timings on an ordinary host, not target
online timings. The first affine attempt recorded `PRODUCER_FAILURE` after
its pair counter remained zero; its source, binary, protocol, output, and
receipt are preserved as `affine_attempt1_*`.

## Work implication and next test

Let the occupancy of nonempty coset `i` be `c_i`. Every selected source code
belongs to exactly one coset, so `sum_i c_i = 132045`. A two-slot rectangular
enumeration covers `sum_i sum_j c_i*c_j = 132045^2` ordered assignments under
every partition. [The checked Lean theorem](RectangleWork.lean) proves this
identity for arbitrary natural occupancy lists; the audits establish the
source-specific occupancy lists. The observed 1.568% reduction applies to
the number of nonempty rectangle setups or compact per-rectangle predicate
calls. An algorithm that expands each selected assignment gains no reduction
in assignment count from this grouping alone.

The next experiment should attach an **exact public-target predicate** to a
compact affine coset description and count whole-coset rejections before
expanding constituent codes. Freeze an unseen ordinary N131 public point,
preserve every accepted witness by independent point-addition replay, and
measure predicate cost plus rejected-assignment count under one worker,
600 s, and 4 GiB. Compare to the same fixed low-bit source and keep
`candidate_id: null` until the full IC pipeline is specified. A result that
only changes source grouping is a component measurement, not a one-target
online comparison.

## Reproduction

The [coordinate protocol](protocol.json), [affine protocol](affine_protocol.json),
[receipts](receipt.json), [affine receipt](affine_receipt.json), independent
[coordinate audit](audit_result.json), and [affine audit](affine_audit_result.json)
bind the frozen input and outputs. From the repository root, rebuild the
workers with `clang++ -std=c++17 -O3 -DNDEBUG` and run `./sage -python` on
`run.py` and `affine_run.py` in a fresh copy of this directory; the existing
one-shot output files are immutable records. Run the pure-Python audits with
`python3 -B` on `audit.py` and `affine_audit.py`. Build the Lean module from
this directory with `lean RectangleWork.lean`. `verify.py` checks the saved
receipts, audit statuses, failure preservation, and source hash without
rerunning measured jobs. The [proof map](PROOF_MAP.md) gives the exact theorem
boundary.
