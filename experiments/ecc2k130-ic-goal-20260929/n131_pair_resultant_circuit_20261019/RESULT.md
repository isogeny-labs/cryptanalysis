# Two-root resultant elimination on the frozen N131 public point

The exact fixed-seed two-pair resultant removes both right-pair reciprocal
root witnesses from the W29 five-pair circuit. The constructed N131 control
satisfies the resulting circuit. The frozen ordinary public query reached its
600-second wall cap with status `BOUNDED_UNKNOWN` under one solver worker and
a 4 GiB sampled RSS stop.

The eliminated right-pair roots remain existentially represented by the
proved four-root product equation in
[PairResultant.lean](../n41_pair_resultant_filter_20261019/PairResultant.lean).
The circuit retains the five source-validity constraints, collision table,
strict code ordering, two left triple-sum links, a right partial-sum wire,
and the final target link. It omits the former ten-output trace parity row
because two output roots are no longer explicit. Any SAT model must be
decoded and checked by the full curve group law before it can count as a
relation.

| Frozen N131 public-point circuit | Original triple-plus-pair | Two-root resultant |
| --- | ---: | ---: |
| Clauses | 266,665 | 439,353 |
| Native XOR rows | 41,826 | 75,456 |
| Formula bytes | 18,008,905 | 23,053,626 |
| Constructed control | passed | passed |
| Ordinary-query status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |
| Parent query wall | 600.051 s | 600.018 s |
| Sampled peak combined RSS | 645,496,832 B | 619,347,968 B |
| Last reported conflicts | 4.716 M | 4.606 M |

Both query timings are terminal wall-cap outcomes, not solved-time
comparisons. The resultant used more clauses and XOR rows than the original
circuit. The constructed control is the same audited N131 group witness in
both runs; the ordinary query uses the same frozen public point and solver
limits. See [protocol.json](protocol.json),
[public_build_result.json](public_build_result.json),
[query_protocol.json](query_protocol.json), and
[query_result.json](query_result.json). `candidate_id` remains `null`.

The first build-monitor attempt used system Python, which lacked the
transitive `psutil` dependency. The second attempt launched a child but
sandboxed process inspection was denied; its child also stopped at the same
missing dependency. Their receipts and stderr are retained. A checked Sage
runtime built the constructed and public circuits. The first public build
then failed a source-hash assertion because importing the builder rewrote a
timing-bearing result. Versioned v1 protocols and result preserve that
attempt. The final builder guards its control execution behind `__main__`,
and the public formula and bounded query use the v2 frozen protocols.

The next circuit experiment keeps one right-pair root and eliminates only
the other by a two-root norm. Its smaller equation is proved and measured in
[the one-root result](../n131_one_root_norm_20261019/RESULT.md).
