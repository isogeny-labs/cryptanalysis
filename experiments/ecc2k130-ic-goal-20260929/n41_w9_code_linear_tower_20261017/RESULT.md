# A rootless final-pair resultant reduces the unpinned N41 five-pair circuit

## Contribution

The final W9 pair root can be removed from the frozen N41 five-pair
public-point circuit while preserving all 71 exact source codes per slot.
The final link becomes a binary-linearized quadratic in the eight code bits
of that pair. The factored circuit has **107,285 AND gates**, down from
**144,139** in the prior target-early quadratic-tower circuit, a **25.6%**
reduction. It also reduces native XOR rows from 19,833 to 15,811 and
variables from 164,053 to 123,218. The archived ordinary relation
satisfies every emitted clause and XOR row.

The unpinned one-worker public query reached its **600-second wall cap**
with no terminal solver status. Its status is `BOUNDED_UNKNOWN`. The
measured circuit reduction is an implementation improvement; the current
monolithic SAT search does not pass the N41 relation gate. The component
retains `candidate_id: null`.

## Exact method and instance

The curve is `EC1N41Ckb1h7d5e80d3c4d0`,
`y²+xy=x³+1` over `GF(2)[u]/(u^41+u³+1)`, with subgroup order
`549756390943` and cofactor four. Five aligned W9 pair slots have
Frobenius rotations `(0,0,12,12,24)`; each has 71 canonical usable codes
and four signed pair states per code. The frozen public point is the
orientation-6 point `(1936680952394,910597499030)`. No source code or
signed state is fixed in the public query. The archived relation's state
IDs `(105,244,66,47,111)` are used only for a positive build control.

Let `z` be the reciprocal x-coordinate of the first three-pair sum and
`w` the reciprocal x-coordinate after adding slot 3. The left three-pair
F4 norm is inherited from the prior circuit. The right `S3(d,z,w)` link
is normed over slot 3's two source roots. For slot 4, the pair law is
`C e²+p e+H=0`, and its target link `S3(e,t,w)` has coefficients
`A=1+(tw)²`, `B=tw`, `D=t²+w²`. Put `M=A H+C D`, `L=A p+C B`, and
`N=B H+p D`. The final condition is `M²+L N=0`.

For every allowed, split pair source, the [checked theorem](PROOF_MAP.md)
proves `M²+L N=C²g(e₀)g(e₁)`, where `g(e)=A e²+B e+D`. Thus the condition
is exact for either source root, including the charts where a divided
product-recovery formula has an exceptional denominator. Expanding gives
`(A D)p²+(B M)p+M²+C H B²=0`, binary-linear in the code product `p`.

## Frozen evidence

The [witness protocol](witness_protocol.json) pins the source and checked
Sage runtime; checked Sage derived the intermediate reciprocal
`w=2127775291906` from the archived signed group relation. The
[build protocol](build_protocol.json) pins all executed dependencies
before construction. The [factored build](build_result.json) completed in
3.400 seconds of builder time with 151,470,080 bytes self peak RSS and
emitted a 10,757,041-byte XCNF. The witness assignment passed all its
clauses and XOR rows. An [expanded form](build_expanded_result.json)
passed the same control but produced 108,966 AND gates and 15,871 XOR
rows, so the factored form was selected before the unpinned query.

The independent [checked-Sage audit](audit_result.json) evaluated all
71 source codes across 67 fixed intermediate charts, including zero,
the public reciprocal, the witness coordinate, and 64 seeded field
elements. On **4,757** cases it matched the resultant exactly to the
product of the two source-root target equations; exactly one case
vanished, the archived positive control. The four central implications
in [FinalPairResultant.lean](FinalPairResultant.lean) build with pinned
Lean 4.34.1 and report only standard foundations under `#print axioms`.

| Unpinned public query | Recorded result |
| --- | ---: |
| Worker / parent caps | 1 thread; 580 s requested solver limit; 600 s enforced parent wall; 4 GiB combined RSS |
| Parent wall | 600.151 s, `WALL_CAP` |
| Sampled solver / combined RSS peak | 96,272,384 / 107,118,592 B |
| RSS samples / monitor failures | 2,918 / 0 |
| Last logged restart / conflicts | 1,280 / about 720,000 |
| Terminal SAT, UNSAT, or model line | none |

The [query protocol](query_protocol.json), [receipt](query_result.json),
and raw solver streams retain exact input, solver and formula hashes,
the enforced stop, and the last search line. These are ordinary-host
search and resource observations. The read-only [terminal verifier](verify.py)
checks frozen hashes, source controls, Lean output, the independent
audit, and the capped query; its [result](verification.json) classifies
this branch `BOUNDED_UNKNOWN`.

## Next experiment

Reducing gate count by a quarter did not bring the monolithic unpinned
search inside 600 seconds. The next N41 gate should use the last-pair
binary-linear equation as a **source-prefix family constraint** before
expanding the first three pair-output choices, and compare charged
whole-family rejection with the existing native group join. Its public
query must recover and independently replay an unpinned ordinary
relation before this approach is promoted to the frozen N131 one-worker,
600-second, 4-GiB relation attempt. The later goal stages remain useful
rank, factor logs, unseen target recovery, and isolated same-point rho.
