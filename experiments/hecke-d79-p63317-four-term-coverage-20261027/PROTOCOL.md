# Frozen four-term residual coverage protocol

## Input and question

The parent p63317 triple audit reports 28 subgroup elements outside all signed three-distinct-source sums of the 40 projected class points. Reconstruct that residual set from the pinned anchored class logs and test whether each residual has a signed four-distinct-source representation. This is a coverage experiment, separate from the earlier retained public target.

## Producer and stop rules

Use the 40 anchored logs modulo 2531 in source-index order. Enumerate all signed triples with `i<j<k`, signs in `(-1,+1)` lexicographic order; retain every triple witness by resulting scalar. Define residual scalars as `0..2530` absent from this triple set, in ascending order. For each residual scalar, probe fourth index `l=0..39`, then sign `(-1,+1)`, and scan the corresponding triple bucket in insertion order. Reject any witness reusing `l`. Stop that scalar on the first distinct-index witness, or after all 80 probes. Continue through all 28 residual scalars, including failures.

Report triple patterns, triple coverage, residual scalars, per-residual probes and witness, full four-source coverage as a separately computed set, and exact source hashes. This is a finite relation-family result; no candidate ID or target online time is assigned.

## Independent audit

Run through the repository's checked Sage launcher after saving `./sage --runtime-info`. Reconstruct projected points from the pinned class points, verify every anchored log against the subgroup generator, enumerate signed triples independently, check that the residual set agrees, verify all reported four-source group equations and scalar replays, and independently enumerate signed four-source scalar coverage. Retain all discrepancies and raw outputs.
