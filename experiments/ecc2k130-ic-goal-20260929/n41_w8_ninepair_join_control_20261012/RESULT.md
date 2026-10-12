# Nine-pair public-point join yields an independent N41 relation

The frozen nine-pair group join found a decomposition of the previously used
N41 public point after 697,702 right probes and 5.129 seconds of local wall
time. Independent checked-Sage replay verified the nine source pairs, their
raw sum, the cofactor-four target projection, and an 18-term folded relation.
Its 18 nonzero columns are disjoint from the earlier six-pair public-point
relation, giving rank two for those two rows together.

The exact instance is `EC1N41Ckb1h7d5e80d3c4d0`, with field
`GF(2)[t]/(t^41+t^3+1)`, curve `y²+xy=x³+1`, subgroup order
`549756390943`, and cofactor four. The transported public point is
`(920359962848, 755404565011)`; its selected raw preimage is
`(344545435656, 924092594889)`. The input and point come from the earlier
[six-pair experiment](../n41_w8_sixpair_mitm_20261011/RESULT.md). This is a
reused point and a restricted, preselected source policy, so the elapsed
time is a same-point method control rather than an unseen-target yield rate.

The source chooses a left triple from slots 0–2 and a right triple from
slots 3–5, each with 140 signed pair states per slot. It adds one of four
signs of edge zero and one of four fixed two-edge prefix panels. The first
accepted hit uses panel `(132,136)` and free state IDs
`(78,20,121,14,50,101,2)`. All nine edge IDs are distinct. The native
program independently checks 128 reference additions on startup, verifies
the raw group sum for the hit, and preserves its full stdout/stderr logs.
The Sage audit rebuilds the source pairs from the 35-edge W8 geometry rather
than trusting the native program's coordinates.

| Frozen stage measure | Result |
| --- | ---: |
| Input/source/binary SHA-256 | `1f99b78210c3` / `b0a74e93f5da` / `b13c1d0cadbf` |
| Reference additions checked | 128 |
| Left-table entries / build elapsed | 2,513,280 / 2.955 s |
| Right probes until first accepted hit | 697,702 |
| Point matches / accepted relations | 1 / 1 |
| Native elapsed at hit / whole runner wall | 4.721 / 5.129 s |
| Child user / system CPU | 2.626 / 0.097 s |
| Peak sampled RSS | 197,787,648 B |
| Distinct source edges / relation terms / nonzero folded columns | 9 / 18 / 18 |
| Rank of this row / rank with prior six-pair row | 1 / 2 |

The [protocol](PROTOCOL.md) fixes the input, source law, binary hashes, one
worker, 180-second wall cap, and 4-GiB sampled RSS cutoff. The [receipt](receipt.json)
and [native trace](stdout.log) preserve the charged execution. The
[checked-Sage audit](audit_result.json) binds the geometry, target fixture,
runtime, prior row, and solver trace hashes. Its replay command was
`./sage -python experiments/ecc2k130-ic-goal-20260929/n41_w8_ninepair_join_control_20261012/audit_sage.py`;
the checked runtime was saved before that job. Two pre-driver infrastructure
failures—the rejected macOS `RLIMIT_AS` setting and the sandbox-denied `ps`
probe—are preserved in [preflight.txt](preflight.txt). The successful run
used process-observation permission and sampled RSS at 0.2-second intervals.

This result validates a seven-free-pair target-conditioned join with two
fixed prefix pairs at N41. It does not estimate natural yield at N131: the
same source law would require much larger explicit tables, while the measured
N131 nine-pair SAT and 131-conjugate terminal-fiber queries both ended
`BOUNDED_UNKNOWN` under their frozen caps. The next N131 gate is an exact
target-conditioned restriction or compressed join that retains this source
control, fits a 4-GiB/600-second local cap, and independently replays an
ordinary public-point decomposition. Measure verified relation yield and
novel rank before factor-log and same-point rho work. `candidate_id` remains
`null` until the complete IC stages and exact factor base are specified.
These local CPU times are exploratory without a host-isolation receipt.
