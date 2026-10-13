# Target-derived right-family GCD on the N41 public point

The public target now supplies the candidate right partial-sum coordinates
before either right source-product pair is chosen. On a frozen four-family
N41 panel, the exact GCD query preserved the known witness and rejected
three same-seed left controls while keeping both complete 32-product right
bins unresolved. An independent checked-Sage group-law replay evaluated
**1,048,576 signed combinations** and agreed with every family decision:
one full public-point witness in the positive family and zero in each
control.

For each left block root `z` and raw public-target reciprocal `t`, the
upper addition equation is a quadratic in the unknown right coordinate `v`:

`(1+(zt)^2)v^2 + ztv + (t^2+z^2) = 0`.

The query enumerates its field roots, then tests each `v` against all 32
first-product values using the GCD of the 32-root second-product polynomial
and the specialized four-atom polynomial `H(p,q,v)`. A positive-degree GCD
decides existence of at least one allowed second product without enumerating
the 32-by-32 Cartesian product for that candidate coordinate. The positive
hit returned the fixture's left reciprocal `1671037747484` and right
reciprocal `401891074226`.

| Frozen left family | Upper-derived right candidates | GCDs | Exact hits | Independent group matches | Internal family wall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Positive | 16 | 481 | 1 | 1 | 9.891 s |
| Slot-0 control 0 | 16 | 512 | 0 | 0 | 8.818 s |
| Slot-0 control 1 | 16 | 512 | 0 | 0 | 10.948 s |
| Slot-1 control 0 | 16 | 512 | 0 | 0 | 12.200 s |

The [four-family protocol](subset_protocol.json) froze source hashes, one
public point, source order, one Sage worker, 180-second phase caps, and a
4-GiB sampled process-tree RSS cap. The checked launcher runtime receipt
was saved before execution. The [query](subset_result.json) completed in
54.769 seconds parent wall, with 42.036 seconds internal total including
0.175 seconds right-bin setup; the [group audit](subset_audit.json)
completed in 22.358 seconds parent wall. Sampled peak RSS was 255,606,784 B
and 262,602,752 B respectively. The monitor could sample the Sage process
but macOS denied recursive child discovery, so the process-tree resource
check is recorded as degraded; these are stage diagnostics on a contended
host.
The [terminal verifier](terminal_verification.json) checks all four cases,
raw-log and source hashes, both phase exits, and the group-audit binding.

The earlier frozen [17-family protocol](protocol.json) reached its
180.227-second parent cap after printing six completed family decisions,
all consistent with the later positive/control subset. Its terminal state
is `CENSORED_TIME`; its raw stdout and [run receipt](query_run_status.json)
are retained. The four-family subset was frozen afterward and has its own
source and timing boundary.

The [proof map](PROOF_MAP.md) gives the readable exactness argument and
checked Lean composition theorem. The remaining N131 gate is to produce
useful left roots and right seed fibers under the 600-second/4-GiB envelope.
The existing N131 W18 fixed-seed right bin has 33,191 products per slot, so
the degree-32 GCD measurements here cannot be multiplied into an N131 cost
estimate without a measured large-bin implementation and source-family
selection rule. This stage retains `candidate_id: null`; final rank,
target-log recovery, and the paired rho metric are recorded only for a
complete candidate.
