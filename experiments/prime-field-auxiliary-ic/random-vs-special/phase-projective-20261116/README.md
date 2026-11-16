# Exclusive core phases and projective scalar arithmetic

Source `59524758ca320597cf8ea2b760a054904c2532ab`; claim
`PCC-20261116-992167`, unsigned/unverified. The [plan](PLAN.md) records the
baseline, requested comparison and acceptance criteria. [pcc:unverified]

`--profile-phases` opts into a disjoint integer-nanosecond partition of the
core target-dependent search, including initialization and local certificate
replay. Scripted-clock tests check repeated phases and final/early-exit tails.
Profiled/unprofiled controls preserve work, row order and complete recovery
when no live duration cap is used; zero-deadline and every bounded stop are
also exercised. The original APIs use a no-op profiler. Clock overhead is
charged, not subtracted. The offline checker rejects invalid partitions,
mixed profiling settings and recovery time in yield mode. [pcc:unverified]

Scalar multiplication now keeps intermediate points projective, with at most
one final affine inversion. Controls compare every point on all nonsingular
F_7 curves and selected F_31/F_127 curves with repeated affine addition,
exercise full-width scalars, and use a separate affine oracle at both requested
large fields. All arms use this same arithmetic. The existing Jacobian-lane
lead in [the separate prime IC protocol](../../../prime-ic-jacobian-relations-20261031/PROTOCOL.md)
concerns a different collector; neither is claimed as a novel mechanism or a
measured speedup here. [pcc:unverified]

| Source-scoped development check | Producer observation |
| --- | --- |
| Stable core | 30 passing checks, including one doctest |
| Rust 1.78 core | 30 passing checks, including one doctest |
| Targeted CLI | Eight passing checks |
| C Montgomery arithmetic parity | Two passing checks |
| Python alignment checker | 13 passing test methods |
| Actual p=127 three-arm reports | Aligned, with exact phase sums |
| Format, strict core/CLI lint, fatal-warning docs on both core toolchains | Pass |
| Original snapshot | All 2,473 file digests match |

All observations above are unsigned producer checks. Full commands, source
labels and exits are in `*.command.json`; full outputs are in `*.log`.
The [validator](validator.json) pins the raw files. It is a consistency receipt,
not execution attestation. The exported reports use the **existing p=127
correctness fixture**, not a fresh 31/61-bit benchmark panel. Their clock
fields and test elapsed times support no performance comparison.
[pcc:unverified]

The [joint projective row follow-up](../joint-row-20261116/README.md) then
executes the next engineering lead from the plan. Its later source/check
scope is separate. Upstream discovery/preparation, complete cold accounting,
panel admission, successful checkpoint upload, CUDA-runner access and
independent signed replay remain outstanding. No fresh benchmark is launched;
all qualified timing/speedup fields remain null. [pcc:unverified]
