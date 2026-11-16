# IC SIMD capability differs between allocations

- **Status:** investigating
- **Kind:** hardware capability / implementation gap
- **Affected work:** [AVX2 protocol](../experiments/ic-prefix-avx2-20261116/PROTOCOL.md), [failed admission report](../experiments/ic-prefix-avx2-20261116/REPORT.md), PR1621
- **Next action owner:** T-6450 implementer
- **Last updated:** 2026-11-16

## Problem

A prepared binary and native correctness result do not establish that a later
cloud allocation supports the same vector instructions. The current timing
allocation lacks VPCLMULQDQ, so it cannot establish a performance result for the
VPCLMUL kernel even though it accepts the same L4 GPU request.

Scope: fixed registered N15/18/21/24/27, prefix dimensions6/7/8/9/10,
fixtures288..311, all24orders of scalar-prefix and three vector chunk sizes.
Admission required positive actual vector_pairs for every vector arm.

## Evidence and uncertainty

[pcc:unverified] Preparation20261116-095638-7a67 passes vector products across59
accepted field widths,100complete first-witness maps and15loader controls on
its allocation. Timing20261116-100738-4069 completes all120quadruples but all360
requested vector arms report zero vector_pairs. Its exposed CPU flags include
AVX2/PCLMUL and AVX-512, but omit VPCLMULQDQ. The runtime guard uses the exact
scalar fallback.480IC+240rho answers replay in existing independent Python
arithmetic. Claim28dc44 is unsigned producer evidence; native claim4e89f7 has
the same standing. Raw records and source hashes remain immutable.

- **Derived conclusion:** a vector speed ratio is not admitted when the kernel
  does not execute. No SIMD runtime conclusion follows from this fallback run.
- **Suspected explanation:** different host CPU generations behind the same GPU
  request; no physical-host identity or allocation-selection guarantee is known.
- **Missing capability:** guarded vector arithmetic that also supports the common
  AVX2/PCLMUL host, or explicit same-host capability admission before timing.
- **Does not establish:** a kernel regression, impossibility, GPU throughput or
  the broad requested performance objective. No host retry/filtering is used.

## What would unblock it

- [ ] Native correctness exercises both VPCLMUL and ordinary128-bit PCLMUL plus
  AVX2 reduction where supported, with exact scalar field and witness controls.
- [ ] A fresh frozen full-pipeline panel requires positive actual vector counts
  on the timing allocation, identifies the executed backend, preserves every
  failure/control, and replays all answers with existing independent arithmetic.

These conditions establish an executable comparison on the recorded CPU class;
physical qualification, signed standing and broader performance scope remain.

## Next discriminating step

Implement an ordinary PCLMUL product backend with four-lane AVX2 reduction,
retaining guarded VPCLMUL for capable hosts and scalar fallback otherwise.
Freeze fresh targets and a new protocol before timing; preserve the failed
initial allocation rather than retrying it under the original protocol.
Success permits actual native timing; no gain is a recorded negative result;
unsupported capability remains a capability failure. Recheck on native receipts
and timing backend diagnostics, not on a GPU label or a preparation receipt.

## Resolution and history

2026-11-16: Named the allocation capability mismatch after admission failed.
Original source2f74aafe134e, prepared binary18ef30c0b4cf21b6068f556952ca153f3535c8166baddeb20cf6520a87a9eb13.
Existing failed-admission evidence is preserved; implementation repair pending.
