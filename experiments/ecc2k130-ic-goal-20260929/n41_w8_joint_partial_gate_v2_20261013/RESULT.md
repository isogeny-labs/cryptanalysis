# W8 joint partial-sum spans saturate at four states per slot

On the frozen unpinned N41 W8 four-pair public relation, the two unresolved
two-pair partial sums already produce the full 40-dimensional trace-zero
cross span in the witness-centered regions when each source slot admits
four signed states. Among 64 sampled region quadruples at that width, 58
had nonempty partial-sum sets and **all 58 passed** the target-conditioned
linear screen; the other six had no valid partial sums and were rejected
before the span test. Every sampled exact group check found zero relations,
while the archived public witness survived at every width. The result
locates a direct W8 boundary for coordinate-span pruning and directs the
next gate toward source-label and group-sign compatibility.

## Exact instance and screen

The curve is `EC1N41Ckb1h7d5e80d3c4d0`, over
`GF(2)[t]/(t^41+t^3+1)`, with public subgroup point
`(920359962848,755404565011)`. The checked four-pair source table has
30,952 signed diagonal pair states per slot at rotations `(0,7,14,21)`.
The gate uses raw public preimage index 1 and reciprocal target
`t=344545435656`. Its independently replayed relation uses state IDs
`(17678,155,6169,16990)` and eight distinct folded columns.

At width `w=1,2,4,8,16,32`, each of four aligned slot regions contains
`w` state IDs. A valid two-pair partial excludes repeated folded columns,
identity, and zero-x points. For each left/right partial family, the worker
spans the reciprocal x-coordinates over `GF(2)` and checks whether `t²`
belongs to the span of `c²`, `d²`, and `(tcd)²+tcd` from basis coordinates.
Every genuine four-pair group sum in these regions passes this necessary
screen. Separately, an indexed full-point join checks exact target equality
and all eight distinct folded columns.

| States per slot | Witness left/right span rank | Witness cross rank | Sampled nonempty regions / 64 | Span rejects / 64 | Exact group hits in sample |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1 / 1 | 1 | 54 | 64 | 0 |
| 2 | 4 / 4 | 16 | 63 | 64 | 0 |
| 4 | 8 / 8 | **40** | 58 | 6, all empty | 0 |
| 8 | 32 / 32 | 40 | 63 | 1, empty | 0 |
| 16 | 40 / 40 | 40 | 64 | 0 | 0 |
| 32 | 40 / 40 | 40 | 63 | 1, empty | 0 |

The 64 quadruples at each width follow the frozen `mt19937_64` seed law
in `protocol.json`; this is a deterministic sample, not a census over all
region quadruples. The witness-centered region is an explicit positive
control and is not part of the 64 random cases. At width four, each side
has only 16 possible two-pair combinations, but its output span has rank
eight and its 64 bilinear cross columns span the full trace-zero
hyperplane. At widths eight and above, almost every sampled nonempty
region has a cross span of rank 40. A full cross span accepts `t²` because
`Tr(t)=0`; rank screening then cannot distinguish a region with a group
relation from a nonempty region without one.

## Reproducibility and correction

The [first frozen run](../n41_w8_joint_partial_gate_20261013/result.json)
tested span consistency even when one partial family was empty. In that
case the other side's square columns can contain the target constant,
creating a false acceptance. Its source, raw result, and monitored receipt
remain unchanged. The versioned worker checks nonemptiness first and adds
`sampled_empty_regions` to each row. The corrected run completed in
5.548 seconds under its one-worker, 120-second, 4-GiB cap, with sampled
combined RSS 33,472,512 bytes and intact monitoring. These are local CPU
diagnostics; the operation counts and rank outcomes are the comparison.

Independent checked Sage rebuilt the witness-centered two-pair sums at
all six widths, verified each rank, cross rank, and exact group hit, and
confirmed that a same-edge width-four left region has no valid partial
sum. Its [audit result](audit_result.json) and [runtime receipt](sage_runtime_info.json)
are bound by a frozen 120-second/4-GiB protocol; the audit completed in
41.611 seconds with sampled combined RSS 225,181,696 bytes. Run
`python3 -B verify.py` for the read-only terminal check of all frozen
hashes, caps, v1/v2 differences, native sample statistics, and Sage
controls. This is a point-decomposition stage with `candidate_id: null`.

## N131 transfer decision

The full cross rank at width four arises even though the two coordinate
spans have ranks only eight each; requiring `dim C + dim D > 41` would
miss this saturation. Increasing a source region therefore loses the
linear target signal well before it saves enough label enumeration to
matter at N131. The next attempt should preserve **source labels and
the sign of each partial point** while coupling two upper S3 links to
the public target. It should measure rejection of nonempty W8 region
families before explicit pair expansion and retain the archived public
relation as an unpinned control. Promotion to the frozen N131 point still
requires an all-stage one-worker work and memory bound.
