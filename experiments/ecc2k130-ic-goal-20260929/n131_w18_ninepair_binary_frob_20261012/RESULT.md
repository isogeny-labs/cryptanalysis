# Binary Frobenius selection removes 133,770 clauses from the N131 target circuit

A two-bit raw-fiber selector and an eight-bit Frobenius exponent now choose
among all **524** target reciprocals using eight controlled linear squaring
maps. This replaces the 524-way one-hot target table while retaining the
same nine free W18 pair slots, exact source gates, 18-distinct-column shield,
and frozen public point. The ordinary XCNF has **133,770 fewer clauses** and
**1,996,260 fewer bytes** than the immediately preceding inverse-trace
variant. The constructed nine-pair assignment satisfies every clause and
native-XOR row. A one-worker ordinary query ran for 600.023 seconds
under the 4-GiB cap and returned `BOUNDED_UNKNOWN`.

## Exact target choice and controls

The field is `GF(2)[t]/(t^131+t^13+t²+t+1)` on `y²+xy=x³+1`, curve
`EC1N131Ckb1heb5f1998f20b`, subgroup order
`680564733841876926932320129493409985129`, cofactor four. Workload
`cc09e7eb202a` supplies one frozen public point
`Q=(1052727368764798954359115163823647684025,
2071227447786120917960296877345506689833)`. The W18 seed-212 source
has 33,191 admissible canonical pair codes per slot; nine slots use rotations
`0,16,...,128`. The full signed-Frobenius factor-base closure has
34,339,816 usable points before folding and 131,068 folded columns under
the prior geometry audit. `candidate_id` remains `null` because this is a
point-decomposition component rather than a fully specified IC pipeline.

For each raw preimage `U_i`, the selector starts with the constant
`a_i=1/x(U_i)`. Bit `k` of the rotation exponent selects either the current
coordinate or its `2^k`-fold Frobenius image. Since field squaring is linear
over `GF(2)`, each image is a fixed XOR map; a mux composes the selected
images. Clauses reject rotation codes 131 through 255. The four raw fibers
remain enabled: the nine-pair outputs have mixed reciprocal traces, so the
two-fiber trace restriction from a different source law does not apply here.

The [N41 pre-promotion control](n41_control_result.json) uses the archived
public nine-pair relation with seven free pair slots and checked Sage to verify all 164 valid
fiber/rotation choices and reject all 92 invalid six-bit rotation codes.
The constructed N131 nine-pair assignment then passes all 472,206 clauses
and 72,493 native-XOR rows in its [control receipt](control_result.json).
After the ordinary search, the [all-choice audit](selector_524_result.json)
evaluated the actual Boolean selector at every one of the 524 N131 choices,
matched the prior independent checked-Sage orbit digest, and rejected all
125 invalid eight-bit codes. The [proof map](PROOF_MAP.md) gives a checked
Lean composition theorem and identifies the remaining concrete-circuit
formalization bridge.

| Ordinary formula measure | One-hot inverse-trace | Binary Frobenius | Change |
| --- | ---: | ---: | ---: |
| Variables | 227,890 | 231,351 | +3,461 |
| AND gates | 153,201 | 154,245 | +1,044 |
| CNF clauses | 605,973 | 472,203 | −133,770 |
| Native-XOR rows | 69,550 | 72,481 | +2,931 |
| XCNF bytes | 16,249,897 | 14,253,637 | −1,996,260 |

## Frozen public-point search

The [protocol](protocol.json) binds the checked N41 control, source and
solver hashes, 524-choice public target, one worker, 600-second total
target-dependent cap, and 4-GiB combined RSS cap before the constructed
control and ordinary query. The [query receipt](query_result.json) records:

| Exclusive target-dependent phase | Measured wall |
| --- | ---: |
| Target orbit and four raw fibers | 0.093465 s |
| Formula construction | 4.577577 s |
| XCNF serialization | 0.070517 s |
| Solver search and stop | 595.279753 s |
| Terminal parse | 0.001406 s |
| **Total attempt** | **600.022718 s** |
| Sampled peak parent-plus-solver RSS | 505,331,712 B |
| Actual restart rows / terminal status lines | 2,379 / 0 |

The [independent terminal audit](audit_result.json) rebuilds the ordinary
XCNF byte for byte, checks the exclusive phase sum and paired workload,
finds active solver restarts with empty stderr, and retains the
`TOTAL_QUERY_TIMEOUT` classification. Both this variant and its same-point
one-hot predecessor ended `BOUNDED_UNKNOWN` under their frozen 600-second
caps. Formula counts are exact; local wall and restart observations are
exploratory on this contended host. The [archive receipt](archive_receipt.json)
binds deterministic gzip copies of both formulas to their raw hashes, and
`python3 -B verify.py` passes after byte replay. Checked
[Sage runtime information](sage_runtime_info.json) was saved before the N41
control. Lean 4.34.1 builds `BinaryFrobenius.binary_target_correct` with
only standard `propext` in `#print axioms`.

The next algorithmic gate is an output-first inverse constraint on **two
unresolved pair outputs** in a target-coupled partial-sum link. Freeze the
positive and negative residuals of the existing unpinned N41 public-point
fiber, count seed/product families rejected before source masks are opened,
and project complete N131 work and memory under the same 600-second/4-GiB
envelope before another ordinary query. A solver model must undergo signed
group-sum, inverse-Frobenius, folded-row-rank, and scalar replay.
