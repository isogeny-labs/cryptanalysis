# Unpinned N41 width-11 five-pair relation and N131 table floor

**A native two-pair-index join found an ordinary five-pair decomposition of
the frozen N41 public point.** Its query selected all source codes and
signs freely; independent checked Sage reconstructed the ten source
points, verified ten distinct signed-Frobenius columns, and replayed both
the raw group sum and its nonidentity prime-subgroup projection. The
one-worker query found the first compatible relation after 396,919 probes.
The target-dependent native join interval was 1.593 seconds after 5.596
seconds of reusable table preparation on this ordinary host.

The exact transfer check gives a second result: an explicit two-pair table
for the proposed N131 width-33 source needs **at least 278,971,932,704
bytes of 16-byte point keys** from an embedded width-20 subset alone.
That is 64.95 times the four-GiB cap before witness identifiers, hash
overhead, or the rest of the pipeline. The N41 relation therefore validates
the join mechanics, while the N131 continuation requires an implicit
right-family operator.

## Curve, source, and frozen query

The N41 curve is `y²+xy=x³+1` over
`GF(2)[u]/(u^41+u³+1)`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`,
prime subgroup order 549,756,390,943 and cofactor four. The public raw
point is `Q=(1936680952394,910597499030)`. The fixed-seed source mask
is 56, with 281 valid canonical width-11 pair codes and four signed pair
outputs per code. The five slots use Frobenius rotations
`[0,0,12,12,24]`; their source parameters and point signs were all free
in the query. Every accepted relation must use ten distinct folded
source columns.

The [preparation protocol](prepare_protocol.json) pins the checked Sage
runtime, exact source census, public fixture, generator, and 128
Sage-computed addition checks. Its [result](prepare_result.json) contains
the hash of all 5,620 rotated signed states in `join_input.tsv`. The
[query protocol](query_protocol.json) pins that input, compiled binary,
source, compiler receipt, one-worker policy, random query seed, 20-million
probe cap, 600-second parent wall cap and four-GiB combined RSS cap before
the native query started.

The native worker indexed every compatible ordered pair in slots three
and four, built a reusable slots-zero-and-one pair list, then sampled a
left pair and slot-two state. For each target-derived residual, it looked
up the exact right pair and checked all ten folded columns and the full
curve group sum before stopping. The [query receipt](query_result.json)
retains the command, stage lines, hit IDs, cap status, stdout/stderr
hashes, parent wall and RSS samples.

| Phase or verification | Result |
| --- | ---: |
| Checked Sage state preparation | 17.736 s; 281 codes, 1,124 signed states per slot |
| Native versus Sage additions | 128/128 passed |
| Right two-pair index | 1,258,720 entries; 3.169 s cumulative native time |
| Reusable left two-pair list | 1,258,720 entries; 5.596 s cumulative native time |
| Target-dependent probes to first compatible hit | 396,919 |
| Target-dependent native relation-query interval | 1.593 s exploratory host time |
| Full native / monitored parent wall | 7.189 / 7.734 s |
| Sampled combined peak RSS | 131,809,280 B |
| Independent checked-Sage relation replay | 10 distinct folded columns; raw and projected sums pass; 3.540 s |

The hit's signed-state IDs are `[112,843,571,278,74]`, with source
codes `[96,783,555,253,63]`. They were not pinned to the archived
relation fixture. The [independent audit](audit_result.json) reconstructs
each source point from its code and sign, verifies the signed-Frobenius
column, checks that the ten raw leaves sum to `Q`, and verifies that their
cofactor-four projections sum to nonidentity `4Q` in the prime-order
subgroup. The row has rank one against an empty unfolded relation matrix.
The [terminal verifier](verification_result.json) binds the frozen
hashes, query caps, hit, replay and transfer calculation.

These are relation-stage measurements on an ordinary host. The 1.593-second
interval includes target-dependent group probes and the hit check; it
excludes the reusable tables and independent audit. The native table
build, checked Sage producer, relation linear algebra, target descent,
scalar replay and same-point rho are separately identifiable stages.
`candidate_id` stays `null` until a complete IC pipeline is specified.

## Exact N131 storage transfer

The proposed N131 width-33 source has the same field model and seed mask
898618 as the exact width-20 source, and its 32 free positions contain
all 19 width-20 code positions. Therefore its valid-code family contains
the 132,045 source codes in the independently verified
[width-20 census](../n131_w20_code_trace_bitset_20261014/RESULT.md).
The exact [width-29 folded-collision census](../n131_w29_folded_collision_20261018/RESULT.md)
has only 2,093 unordered valid collision pairs in the larger containing
source. Selecting just one signed state per width-20 code yields at least

`132045×132044 − 2×2093 = 17,435,745,794`

compatible **ordered** right pairs. The first term excludes equal codes;
the second allows both orientations of every known folded-column
collision, even if all were within the width-20 subset. At 16 bytes per
point key, those pairs require at least 278,971,932,704 bytes. The
[projection receipt](projection_result.json) pins the source identities
and exact arithmetic. The [Lean proof map](PROOF_MAP.md) records the
checked storage implication and the finite-source bridge.

This memory floor applies to materializing the native two-pair index.
An implicit membership operator or a different joint algebraic solver
could use far less memory. The next experiment should retain the
source-product variables and public residual in one compact free-code
constraint, and measure whole-family rejection before enumeration. An
N131 public query should follow only after that representation passes an
unpinned N41 control and its projected one-worker resource gate.
