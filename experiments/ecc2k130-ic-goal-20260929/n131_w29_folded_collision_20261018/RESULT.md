# Exact folded-column exclusions for the N131 W29 source

The canonical W29 source on `EC1N131Ckb1heb5f1998f20b` has **2,093
distinct valid code pairs** whose two-point source columns share a signed
Frobenius orbit. All other cross-code pairs have disjoint folded columns.
The resulting finite table makes exact distinct-column constraints
practical in a full-domain N131 point-decomposition circuit.

## Geometry and exact enumeration

The field is `GF(2)[u]/(u^131+u^13+u²+u+1)` and the curve is
`y²+xy=x³+1`. A canonical W29 source parameter `a` belongs to the
28-dimensional binary space `W` spanned by the unpinned source basis in
[audit_result.json](audit_result.json). Its paired parameter is `a+s`,
where the fixed seed polynomial has integer encoding `s=1797236`.
The actual source point has x-coordinate
`x(a)=1+1/halftrace(a)`. This map is injective for admissible `a` and
commutes with Frobenius. Thus two source columns share a signed
Frobenius orbit exactly when, for some `k∈{0,...,130}` and endpoint
choices `e,f∈{0,1}`,

`Frob^k(a+e·s)=b+f·s` for canonical codes `a,b∈W`.

For each `k,e,f`, the left side is binary linear in the 56 code bits,
with constant offset `Frob^k(e·s)+f·s`. The [frozen audit](protocol.json)
solves all 524 affine systems, retains an exact solution and kernel for
every feasible one, and counts its `2^(56-rank)` code pairs. Its
[result](audit_result.json) gives rank 56 in 488 cases and finds 14
cases with a nontrivial pair, including two same-code cases at `k=0`.
For distinct codes, nontrivial overlaps occur only at Frobenius
distances `±1, ±2, ±3, ±4`.

The [validity filter](filter_result.json) enumerated 33,096 code-pair
occurrences in the 12 nontrivial nonzero-distance cases. It retained a
code only when both source endpoints were nonzero and the exact
source conditions `Tr(a)=Tr(a/p)=Tr(s/p)=0` held for
`p=a(a+s)`. These are equivalent to `Tr(a)=0` and
`Tr(1/a)=Tr(1/(a+s))=0`; the latter are the curve-point conditions for
the halftrace x-coordinate map. The filter found 4,186 valid
occurrences, collapsing to 2,093 unordered code pairs. The source
trace conditions and every orbit equation were independently replayed
using Sage's finite-field arithmetic; [verification_result.json](verification_result.json)
compares the complete 524-case rank/feasibility table and the full
2,093-pair set.

| Frozen stage | Exact scope | Result | Arithmetic wall |
| --- | ---: | --- | ---: |
| Orbit linear algebra | 131 Frobenius powers × four endpoint choices | 524 checked affine systems; 14 nontrivial cases | 13.409 s |
| Valid-source filter | 33,096 code-pair occurrences | 2,093 distinct valid collision pairs | 1.157 s |
| Independent Sage replay | All 524 systems and all enumerated pairs | Exact agreement | 6.310 s |

These are ordinary-host algorithmic measurements from the
[checked Sage runtime](sage_runtime_info.json), with startup excluded.
The result is a source-geometry and constraint-construction stage;
`candidate_id` remains `null`. The [proof map](PROOF_MAP.md) records
which structural implications are checked in Lean and which concrete
finite-field matrices remain computational certificates.

The next step is to exclude equal codes and both orientations of each
of the 2,093 cross-code pairs in the aligned five-pair public circuit,
preserve the constructed N131 witness, and run an ordinary public-point
query under one worker, 600 seconds, and 4 GiB.
