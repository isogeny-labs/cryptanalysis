# Matched signed-sumset null protocol

## Question and frozen statistic

The p63317 class projection has 40 distinct nonzero subgroup logs, closed under negation, and contains the anchored orbit `{1,-1}`. Test whether its signed three-distinct-source coverage and the gain from one fixed `−B₀` fourth source differ from a matched random-base control. This is a finite additive control, not a target-recovery or runtime comparison.

For each base, enumerate all `C(40,3)·2³ = 79,040` signed triples with distinct indices. Let `T3` be the covered scalar set modulo 2531. Let `T3_without_0` use only triples avoiding source index 0. The fixed-translate family is `{x−1 mod 2531 : x ∈ T3_without_0}`. Record `|T3|`, the additional coverage of the translate, and whether the union covers the entire subgroup. The class-point base is the observed arm.

## Matched null and stop rule

Use Python's `random.Random` seeded by the integer SHA-256 digest of the literal UTF-8 string `hecke-d79-p63317-sumset-null-v1`. For each of 256 independent draws, sample 19 distinct representatives without replacement from `2..1265`, retaining draw order. Construct the 40-log control as `[1] + representatives + [2530] + [2531−representative for each representative]`. Thus every arm has the exact anchor, 20 sign orbits, 40 distinct nonzero logs, and negation closure. Retain every draw and every measured row; do not discard outliers or redraw.

Primary comparison: observed triple coverage versus all 256 controls. Secondary comparisons: fixed-translate gain and full-union frequency. Report both empirical tail fractions using `(1 + tail_count)/(257)` to avoid zero estimates; report raw control range and quantiles. The control tests only this matched additive model, not all isogeny or modular constructions.

## Independent audit

Verify all pinned parent inputs, reproduce the 256 sampled orbit lists from the seed, recompute every row with an independent enumeration, and compare all statistics and aggregate counts. The parent checked-Sage group audit supplies the curve-point interpretation of the observed class logs.
