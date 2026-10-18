# Target-conditioned quartic roots on N41 and N131

For a fixed first pair product `p`, the 13-term target resultant becomes
a quartic in the second pair product `q`. Exact field-root extraction
recovered the audited N41 source pair `(253,63)` while enumerating all
281 valid first codes on the constructed target and the first ordinary
target. The N131 panel recovered the independently replayed positive
pair `(3,16722)` and supplied a matched public-point timing panel.
Every one of the 712 quartics in these two panels had degree four and
four distinct field roots. This observation led to the faster direct
curve-state construction in the [next experiment](../resultant_direct_products_20261018/RESULT.md).

## Frozen inputs and checks

| Panel | First-code input law | Targets | Queries | Source-span hits |
| --- | --- | --- | ---: | --- |
| N41 smoke | first valid code 253 | constructed positive | 1 | `(253,63)` |
| N41 unpinned control | all 281 valid W11 codes | constructed positive; frozen ordinary index 1 | 562 | `(253,63)`; none on ordinary |
| N131 W33 | code 3 plus 256 distinct deterministic 32-bit codes, then exact source-validity filter; 75 valid codes total | constructed positive; frozen public point | 150 | `(3,16722)`; none on the public panel |

The N41 pair results match the independent complete finite-domain
census on both targets. The N131 positive pair is bound to the earlier
independent Sage point and group replay. The N131 public row reports
only this frozen 75-code first-source panel. The exact field, curve,
rotations and coefficient hashes are in `protocol.json`; the N131 query
was gated on the complete N41 control by `n131_gate.json`.

## Measured stage costs

| Panel | Root extraction sum | Median root extraction | Full monitored wall | Sampled peak combined RSS |
| --- | ---: | ---: | ---: | ---: |
| N41, 562 queries | 29.118 s | 0.0470 s/query | 39.126 s | 248,414,208 B |
| N131, 150 queries | 208.913 s | 1.406 s/query | 219.418 s | 250,494,976 B |

These are one-worker ordinary-host diagnostics under a 600-second and
4 GiB bound, including every first-code query in each frozen panel.
The root-time sum excludes field setup, coefficient grouping, and
span decoding; the monitored wall includes them and checked Sage
startup. `candidate_id: null` records the unresolved factor-base size
and complete IC pipeline. The first runtime-receipt command failed at
shell redirection before Sage launched because this directory did not
yet exist; `runtime_attempt0.json` preserves that producer failure.

Run `python3 audit.py` here to check the pinned inputs, N41 promotion
gate, all query counts and terminal receipts.
