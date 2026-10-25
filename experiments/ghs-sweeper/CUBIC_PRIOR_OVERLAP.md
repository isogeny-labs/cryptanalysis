---
title: "Five-gluing novelty audit: all selected source classes overlap history"
date: 2026-10-25
geometry: margin=0.85in
fontsize: 10pt
---

**All 12 source trace/isogeny classes selected by the new five-torsion
screen were already present in the retained genus-three sweep. No new
local source isogeny class was found.**

This is a supplement to [the census and proof report](CUBIC_GLUING_RESULTS.md).
It resolves the local-history question left open by that snapshot. The
[module classification](CUBIC_GLUING.md) and [sufficient geometric criterion](FIVE_GLUING_GEOMETRY.md)
remain derived written results; their publication priority remains unresolved.
The user's requested novel affected family has not been established.

## Read-only historical comparison

The completed exact source census selected 252 full-degree F512/F8 models,
forming 126 twist pairs and 12 source trace classes. We compared those exact
traces with saved genus-three, base-degree-three candidates in the pre-existing
`runs/smoke.sqlite`, retaining only raw-verified cover models and independently
verified source orders. The lookup scope was frozen at `dee8ef6e` before
the bulk comparison. No search job or timing campaign was run.

| Source trace | Verified historical cover-model matches |
|---:|---:|
| -43 | 3 |
| -37 | 9 |
| -23 | 36 |
| -17 | 30 |
| -13 | 27 |
| -7 | 45 |
| 7 | 45 |
| 13 | 27 |
| 17 | 30 |
| 23 | 36 |
| 37 | 9 |
| 43 | 3 |

These counts enumerate historical cover-model rows, not independent elliptic
families or successful attacks. Each trace has a retained witness containing
its exact spectral model ID, model JSON, source JSON and verification flags.
The database SHA-256 is
`8290f8fbb6abc6c2e16e8ce30484c45d979c785e2098d4332f1e1478e621bd1c`.
The exact SQL and all witnesses are saved in
`cubic-gluing-checks/five-only-historical-overlap.json`.

![Verified historical matches for every selected trace. This is an exact journal lookup, with no sampling uncertainty or large-field extrapolation.](cubic-gluing-figures/historical-overlap.pdf){width=92%}

## What the overlap establishes

For elliptic curves over the same finite field, equality of trace identifies
the same rational isogeny class. It does not establish equality of the exact
coefficient b or a checked map between the saved source representative and
our new source model. The old records are spectral/source matches and retain
`explicit_map_to_target_verified=false`. They supply no explicit old transfer
to substitute for the missing new quotient map.

The five-torsion predicate selects models excluded by the earlier
three-torsion predicate. Its source trace classes are nevertheless already
in the broader historical genus-three screen. A different recognition rule,
an alternate quotient and a new local source class are separate statements.
Only the recognition rule and the stated existence implication have been
derived here. No previously unknown vulnerable family, useful cost advantage,
or evaluated five-gluing attack is claimed.

![Evidence boundary after the historical lookup.](cubic-gluing-figures/overlap-scope.pdf){width=85%}

The full Tian 2023 primary-text comparison remains unfinished, and Hess's
generalized descent remains the broad binary baseline. The next construction
obligations on b=48 are actual E[5] coordinates, quotient reconstruction,
arithmetic twist selection and an evaluated prime-subgroup/log map. Those
steps could establish a different explicit correspondence; they do not erase
this historical source-class overlap.

The previous 89-file manifest and all earlier reports remain unchanged.
This supplement has its own additional-artifact manifest. The original curve
catalogue and verified attack-route graph receive no new entry from this result.
