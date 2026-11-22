# Frozen local panel results

Date: 2026-11-18

Status: complete local execution of the prospectively frozen panel under the
owner's narrow local-run waiver; results are not independently PCC-verified.
[pcc:unverified]

## Execution receipt

The exact command in `PROTOCOL.md` completed all 1,600 scheduled trials in
660.404892206192 seconds.  The frozen analyzer reports 1,205 `ok` rows, 389
`small_order` exclusions, and 6 `no_integer_solution` exclusions.  No
unexpected status, certificate failure, group-arithmetic failure, subprocess
failure, or censored suffix was observed. [pcc:unverified]

Retained artifact digests are:

```text
2226d6fdfb56f87022eac8ed5ee7f38ad1e115375aaa057d69dfe67c40f3f773  run/rows.jsonl
aa67068680ea2d6d3fb633a76c2a834410d47b264bf5f95753fe7833dfb35f8a  run/summary.json
```

## Primary estimands

Every eligible row had the necessary finite-field relation.  The exact lifted
plane-cubic test certified 67 rational relations, of which 23 had an
invertible target coefficient and correctly recovered the planted logarithm.
[pcc:unverified]

| selected points | scheduled | eligible | certified relation | relation / eligible | recovered target | recovery / eligible |
|---:|---:|---:|---:|---:|---:|---:|
| 6 | 400 | 322 | 9 | 2.80% | 5 | 1.55% |
| 7 | 400 | 310 | 16 | 5.16% | 4 | 1.29% |
| 8 | 400 | 292 | 18 | 6.16% | 7 | 2.40% |
| 9 | 400 | 281 | 24 | 8.54% | 7 | 2.49% |

The preregistered implementation/feasibility boundary is therefore met:
`r=7..9` produced exact relations, the arbitrary chord-origin certificate
survived source reduction, and all three new ranks recovered planted target
logarithms.  The `r=9` relation yield was 3.05 times the `r=6` yield among
eligible rows in this bounded panel. [pcc:unverified]

## Diagnostic contrasts

The balanced coordinate lift produced 61/596 certified relations (10.23%)
and 21/596 recoveries (3.52%).  The wide lift produced 6/609 relations
(0.99%) and 2/609 recoveries (0.33%).  This roughly tenfold descriptive
contrast is a follow-up lead, not a prospectively specified causal or
asymptotic claim. [pcc:unverified]

The certified-relation rate decreased across the field panel: 32/197 at
`p=31`, 23/304 at `p=67`, 9/341 at `p=127`, and 3/363 at `p=251`.  That trend
does not overturn the classical conditional `O(1/p)` obstruction and does not
establish an ECDLP speedup. [pcc:unverified]

Of the 67 certified relations, 44 had target coefficient zero.  The other 23
had target coefficient `-1` or `1`, and every one correctly recovered the
target.  A target-bearing relation enumerator is therefore the next concrete
algorithmic hypothesis, but it must be evaluated in a separately frozen
fresh-seed panel because this observation is post-outcome. [pcc:unverified]

## Claim boundary

This is a real implementation and toy-feasibility result: it demonstrates
certified nine-point lifted relations and exact target recovery without
sacrificing a selected point as the group identity.  It is not yet the large
Xedni-calculus breakthrough requested by the owner.  That requires a fresh
confirmatory panel, complete charged-work accounting, matched end-to-end
Pollard-rho comparison, and independent verification. [pcc:unverified]
