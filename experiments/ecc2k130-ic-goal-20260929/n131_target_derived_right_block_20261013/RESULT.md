# N131 public-point right-block completion with a supplied left block

The frozen N131 W18 experiment recovered a complete eight-column relation
from one constructed public point and a supplied left four-atom block. The
public point yielded four raw preimages and eight right-block reciprocal
candidates. Eight complete native scans of the right source bins processed
262,616 first-product states, found one degree-one GCD, and a separate
checked-Sage audit decoded the right masks `(19,22)` and `(24,25)`. It
verified all eight distinct folded columns and the public group equation
after testing all 256 signed assignments. The [terminal receipt](terminal_verification.json)
checks frozen hashes, raw logs, phase sums, caps, and the audit result.

## Method and source

The exact curve is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t^131+t^13+t^2+t+1)`, with Koblitz model
`y²+xy=x³+1` and subgroup order
`680564733841876926932320129493409985129`. The public point is recorded
in [protocol.json](protocol.json). This is a constructed correctness
control: the left-block reciprocal
`1397139031383803385761202952286479025964` came from the frozen source
fixture. All right-block candidate coordinates were derived from the public
point and that supplied left reciprocal. The right source was fixed to W18
rotations 64 and 96, seed masks 5 and 1, and the exact
`support_w18.tsv` source.

The checked Sage derivation computes the four preimages of the public point
under multiplication by four, including the four-torsion coset. For each
nonexceptional raw preimage reciprocal `t` and supplied left reciprocal `z`,
it solves the right-coordinate quadratic

`(1+(zt)²)v² + ztv + (t²+z²) = 0`.

The frozen input yielded two distinct roots per preimage. For each root,
the native scanner iterated all 32,827 usable first products of the first
right slot, tested a degree-at-most-eight GCD against the 131,072-element
linearized superset of the second right slot, and applied the exact source
filter after decoding a root. Only candidate 5 produced a GCD hit. The
group auditor recovered both source mask pairs without reading their
identities from the fixture, then checked every sign assignment and
`[4](L+R)=Q` on the public point.

## Frozen measurements

| Stage or resource | Result |
| --- | ---: |
| Target-derived raw preimages / right roots | 4 / 8 |
| Complete native right scans | 8 / 8 |
| First-product states per scan / total | 32,827 / 262,616 |
| Native raw GCD hits | 1, in candidate 5 |
| Right source pairs / folded columns | `(19,22)`, `(24,25)` / 8 distinct total |
| Signed assignments / public group matches | 256 / 1 |
| Parent target-derivation wall (`T_target_query`) | 15.687090083 s |
| Parent native-scan wall (`T_target_PDP`) | 212.056472958 s |
| Unassigned runner overhead / pipeline parent wall | 0.105849084 / 227.849412125 s |
| Separate checked-Sage group-audit parent wall | 14.135893625 s |
| Sum of the two separate parent intervals | 241.985305750 s |
| Pipeline / audit sampled combined peak RSS | 284,573,696 / 307,658,752 B |
| Envelope | one worker; 600 s pipeline, 120 s audit; 4 GiB RSS each |

The audit was launched as a separate frozen job after the pipeline. Its
time is reported separately and the summed intervals are an accounting
convenience, not a measured contiguous online run. The remaining IC stages
have no run values; `candidate_id` and primary one-target online time are
`null`. The host has no isolation receipt, so wall values are stage costs
under this run's conditions. The exact commands, native binary, compiler,
checked Sage runtime, and source hashes are in the three frozen protocols
and their raw receipts.

## Fixed-left coverage bound

The two right slots have 32,827 and 32,842 usable unordered mask pairs in
the [independently checked source bridge](../n131_linearized_superset_preflight_20261013/result.json).
Each pair has at most four signed versions. For one fixed left block, every
reachable public target therefore lies in the image of at most
`16 × 32,827 × 32,842 = 17,249,669,344` labelled right choices. Collisions
and distinct-column exclusions can only reduce the image. For a uniform
point in the stated subgroup, the probability of coverage is at most the
exact fraction

`17,249,669,344 / 680,564,733,841,876,926,932,320,129,493,409,985,129`

or approximately `2.53461 × 10^-29`. This is a counting bound for the
declared fixed-left, fixed-seed source law, independent of assumptions about
randomness in the group map. The constructed input deliberately lies in its
image. [FixedLeftCoverage.lean](FixedLeftCoverage.lean) checks the general
finite-image step; the [proof map](PROOF_MAP.md) records its exact scope.

The next gate must generate or constrain left and right source families
jointly from an unpinned public point. A proposed filter should prune whole
families while at least two pair domains remain free, preserve the N41
ordinary witness, and receive a source-bound N131 whole-search cost before
a 600-second ordinary query. Repeating these eight fixed-left scans on an
ordinary point would have the small coverage quantified above.
