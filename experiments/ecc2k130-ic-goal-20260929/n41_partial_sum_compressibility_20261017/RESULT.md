# Exact N41 three-pair partial-sum index and negation census

An exact sorted index recovered the archived six-pair public-point relation
while using **146,079,744 bytes sampled combined peak**, versus
247,955,456 bytes for the earlier hash join. It took **11.356 s** parent wall
on the ordinary host, versus 6.927 s for the earlier join. Both used the
same frozen 960 signed source-pair states and public raw point
`(2026560328086,1928332930914)` on `EC1N41Ckb1h7d5e80d3c4d0`.

The full left-side census exposes an exact compression opportunity: every
observed x-coordinate occurs with both point signs. The 3,750,144 admissible
left triples yield 3,750,136 distinct points and 1,875,068 distinct
x-coordinates. There are eight repeated point rows; every one of the
1,875,068 x-coordinates has both y-values. A separate audit checks that all
960 source-pair states form 480 sign-flip pairs with unchanged folded columns.

## Method and measurements

The native program enumerates internally column-disjoint triples from the
first three slots, sorts their exact raw point keys, and builds a 16-bit
x-prefix directory. It then enumerates right triples and searches the exact
key `Q-R` within its directory range. A hit is accepted only after full
point equality, twelve-column disjointness, and group addition replay. The
first accepted state IDs are `(12,122,116,47,128,34)`, identical to the
archived independently checked-Sage relation.

| Frozen stage | Value |
| --- | ---: |
| Left rows before sorting | 3,750,144 |
| Distinct points / distinct x | 3,750,136 / 1,875,068 |
| Distinct x prefixes at 8, 16, 24, 32, 41 bits | 256; 65,536; 1,774,282; 1,874,644; 1,875,068 |
| Left enumeration / sort and census completed | 6.177 s / 7.066 s process elapsed |
| Accepted hit / parent wall | 11.078 s process elapsed / 11.356 s |
| Right probes before hit | 1,100,323 |
| Sampled combined peak / native self peak | 146,079,744 B / 121,896,960 B |

The native run had one worker, a 60 s parent cap, and a 4 GiB combined RSS
cap. It completed with a healthy monitor. The first system-Python runner
invocation stopped at import because `psutil` was unavailable there; its
reproduced failure log is retained. The successful runner used the checked
repository Sage launcher for the Python parent. The compiled C++ program
itself uses the archived field and group operations. Source, input, binary,
compiler flags, stdout, stderr, and the old comparison receipts are bound in
`protocol.json`, `run_result.json`, and `verification.json`.

## Structural result and next test

On `y²+xy=x³+1`, point negation preserves x and maps `(x,y)` to
`(x,y+x)`. Flipping both endpoint signs of a source pair negates its pair
sum and preserves its two columns. The checked [Lean result](NegationQuotient.lean)
shows that negating three pair sums negates their partial sum and gives the
exact either-sign target lookup. The [proof map](PROOF_MAP.md) separates this
group statement from the finite source-state audit.

The next exact variant will enumerate one source triple per global sign
pair, store its full point and three state IDs, and test both `P` and `-P`
at target lookup. This can halve left-side enumeration and index rows while
preserving every admissible relation. Measure same-point recovery, complete
run time, memory, and replay against this frozen result. The factor-two
quotient alone does not supply the exponential reduction needed at N131;
the following gate must expose stronger target-dependent pruning before
promotion. The IC pipeline remains `candidate_id: null`.
