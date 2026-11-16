# Current-baseline native IC comparison

## Request and requirements

Optimize the cryptanalysis index-calculus code using specialized arithmetic
and algorithmic reductions; establish a measured improvement against the
current implementation. Preserve the broader elliptic-curve and GPU scope. [pcc:unverified]
The present finite-field implementation is one component of that objective.

| Requirement | Evidence to collect |
| --- | --- |
| Preserve current implementation and checkpoint recovery | Current-upstream source base; full C suite; journal/cache tests |
| Improve one-target online computation | Same-point baseline/candidate pairs, raw first-solve intervals and independent modular-power replay |
| Reduce setup work where possible | Separately timed setup, matrix dimensions, iteration counts and all verified factor logs |
| Preserve portable native operation | Local ARM64 unit checks and fresh physical x86-64 build |
| Qualify performance | Frozen allocation, GPU-host identity, pinned CPU, source/binary hashes, A/A calibration, cgroup and scheduling counters |
| Establish independent claim standing | PCC claim and signed verifier verdict; producer reports remain unverified |
| Broader elliptic-curve IC/GPU acceleration | Remains open; no finite-field measurement substitutes for it |

## Frozen baseline and candidate

Baseline is upstream cryptanalysis commit
2b97ddf662b53d330581ae51a7818a82e94585ac. It already contains inverse-based
four-prime smoothness scanning, compact relation storage, durable journals,
checkpointed precomputation, Shoup-based modular products and threaded Lanczos.
The candidate retains those components and changes indexcalc.c only:
signed rational individual-log reconstruction, reusable Montgomery step powers,
and exact spanning-forest elimination of linear-sieve auxiliary columns.
No replacement of current linalg.c is admitted in this comparison.

The earlier comparison on codex/single-target-ic-metric used an older branch.
Its frozen records remain historical producer reports; its timing ratios do
not establish the gain against this current baseline. [pcc:unverified]

## Inputs and accounting

Freeze moduli 2000000579, 1099511627791, 281474976710597 and
14636773816760213 with the linear-sieve collector; include a random-exponent
control at 2000000579. Use automatic base/radius policy, collector seed 12345,
one thread and five previously unused fixture indices 10 through 14.
For each modulus set g=the primitive root, and construct the public point
outside timing as h=g^x mod p, with
x=((0x23456789abcd + fixture*0x9e3779b97f4a7c15) mod 2^64) mod (p-1).
Keep each pair on the exact same g,h,p. Independently recompute modular
powers in the Python controller; no result boolean alone discharges replay.

The primary interval is the first one-target call to ca_ic_log, including
internal answer checking; a separate modular-power replay follows. Setup is
the entire ca_ic_precompute call and remains separate. Repeat solves of the [pcc:unverified]
same point are optional secondary diagnostics, each retaining its own interval;
their average never replaces the primary first-solve measurement.

## Placement, controls and stopping

Run native correctness locally. Performance runs execute on a CUDA-capable
allocation as host-only controls and explicitly record that the measured
kernel uses the CPU. Rebuild on that allocation. Cap an allocation at four
requested CPU cores, 8 GiB, one L4 GPU and 900 seconds. Use one CPU in the
exposed affinity mask for both arms; record all exposed limits and GPU identity.
Do not start a standing pod or another allocation to replace a noisy pair.

Alternate variant order by fixture. Calibrate the same fixed modular-arithmetic
A/A workload before and after each pair; its fixed iteration count is declared
in the controller before launch. Accept calibration only when the ratio of
pre/post per-process CPU time is within 0.85..1.15. Keep every arm and retain
all rejected/noisy/capped cells. Record CPU/wall times, peak RSS, involuntary
context switches, cgroup throttling/memory events and CPU steal counters.
A zero duration is invalid. A timeout is terminal for that arm, not a zero cost.
The A/A kernel is exactly 5,000,000 chained Montgomery multiplications modulo
18446744073709551557 with multiplier 1234567; compare its checksum as well
as process CPU time. Reject an increase in selected-CPU steal counters.
Require all five same-point answers to replay, calibration to pass, no OOM or
quota crossing, and a 95% paired interval wholly above 1 for a tier-qualified [pcc:unverified]
baseline improvement. Full IC-versus-rho promotion additionally requires the
matched strong-rho/precomputation-rho reference and existing accounting gates;
a missing reference leaves that claim open, not zero.

The reference program implements prime-power Pohlig--Hellman with one
single-target rho solve per large-prime digit and reusable BSGS tables for
prime factors at most 4096. Its factorization, subgroup construction, inverse
base and small tables precede timing. Target cofactoring, digit recovery,
CRT and replay are charged. Rho has a 50,000,000-operation cap per digit and
one thread. A second control uses Bernstein--Lange tables for the large-prime
digits, with separate setup and online timing and 5,000,000-operation setup
and online caps. Capped controls retain their statuses and leave their ratios
null. These reference controls also require independent modular-power replay.

## Prior sources checked

KB revision 9141e386254340a9bdba3036f2bb706a, refreshed 2026-11-14.
- source:eaf47d03c9e59c3751b63304be093564 — crypto-autoresearcher:experiments/EXP-RELN-f3a133/specification.yaml @ fc70d15bb6e41544c5194eae9b70e45a83f1eb2b. Published internal analysis, evidence level none. It requires exact projection and preserving all rows; a chosen cycle proxy is insufficient.
- source:08f3e36526264f46e4eca5d5381c7e31 — crypto:docs/ic/FRAMEWORK.md @ d390e84ab2973372534120fc4207fb65e52d4f3f. Published internal analysis, evidence level none. It records existing CADO-style forest filtering and charged solver alternatives.
- source:7c4d1eb142fa77b4461c35fb27cab63a — crypto-autoresearcher:ledger/proposals/IDEA-20260906-f9f8c8.yaml. Published proposal, evidence level none; no novelty claim is inferred.
Queries also covered rational reconstruction individual logarithms and negative
forest/fill outcomes. Search relevance is not mathematical evidence.
