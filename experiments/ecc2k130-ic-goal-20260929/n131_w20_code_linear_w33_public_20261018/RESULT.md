# Independent full-source classification of the W33 public two-pair residual

**The native code-linear scan and the NTL block-norm computation agree on the
same frozen N131 public point and the same complete 132,045-code W20 source:
the two-pair resultant has no source-code zero.** The code-linear scan checked
264,090 left reciprocal roots and produced zero right-product-span hits in
3.405 seconds of target-dependent native query time. The NTL computation
covered all 132,045 second-code positions across 33 degree-zero block GCDs.
The two paths use different algorithms and source-membership representations.

The [cross-audit](audit_result.json) binds the exact point
`(877610862732227974378969808549299291499,
2063336771837286479337213121437715536874)` to both inputs. Its reciprocal
is `770794657550069419943936485965613853151` in
`GF(2)[u]/(u^131+u^13+u²+u+1)`. The 13 public coefficients in the
[block-norm input](../n131_w20_block_norm_20261018/coefficients.tsv) equal
the coefficients in the [W33 public export](../n131_w33_freecode_resultant_20261018/coefficients.json).
The code-linear fixture's chart value is
`2160830939097265115946515685140930399471`. The worker applies
`standard(z)=z/(z+1)`, which maps that value to the public reciprocal above.

The audit independently rebuilt the complete W20 code set from all 524,493
support rows: `a<a XOR 898618`, both masks supported, and different folded
columns. Its 132,045 codes exactly match every set bit in the code-linear
validity bitmap. It checked the prior code-linear completion receipt and
its independent verification, plus the two block-norm receipts' disjoint
public ranges 0–19 and 20–32. The first block-norm run remained
`BOUNDED_UNKNOWN` at its 600-second cap; the continuation completed the
remaining 13 blocks in a separate run. The union is an exact source
classification, not a single-run 600-second result.

| Exact method | Public work covered | Public zero set | Recorded time boundary |
| --- | ---: | ---: | --- |
| [Code-linear scan](../n131_w20_code_linear_right_20261017/RESULT.md) | 264,090 left roots; all 132,045 right codes represented | empty | 3.405 s native query; 10.749 s parent for setup, positive and public queries |
| [NTL block norm](../n131_w20_block_norm_20261018/RESULT_PUBLIC_REMAINDER.md) | 33 blocks; all 132,045 second codes | empty | 20 blocks in capped first run, 13 in 218.818 s continuation parent |

These ordinary-host component times have different boundaries and host
conditions. They establish exact agreement of the source decision and show
that a two-pair block-norm search is the wrong place to spend more of the
600-second budget while the code-linear kernel is available. The frozen
full challenge point and the remaining pair slots define the active
relation-search gate; this residual classification is a component control.

## First attempt and correction

The [first new fixture](fixture.txt) supplied the public reciprocal directly
to `code_linear`, although the worker expects the preimage under
`standard(z)=z/(z+1)`. Its [frozen protocol](protocol.json),
[native output](native_result.json), and [parent receipt](receipt.json) are
preserved. The worker completed its input, but that input mapped to the
different reciprocal `2160830939097265115946515685140930399471`.
The audit classifies this attempt as `INPUT_CHART_MISMATCH`; its zero-hit
output is excluded from the public-point result. The prior archived
code-linear run supplies the correctly charted, fully scanned point.

## Next search gate

The code-linear oracle solves a supplied two-pair residual in linear work
over the left source, so repeating its search on isolated residuals cannot
generate a seven-pair relation within the envelope. The next experiment must
constrain at least two still-free pair products jointly with the public
target **before** enumerating their Cartesian combinations. An unpinned N41
public relation and an independent point-addition replay are the first gate;
only a source-bound method that fits one N131 worker, 600 seconds and 4 GiB
should be run on the full frozen public point. The current component keeps
`candidate_id: null`.

Run `python3 audit.py` from the repository root to replay the exact source,
chart, coefficient, hash and coverage checks pinned in
[`audit_protocol.json`](audit_protocol.json).
