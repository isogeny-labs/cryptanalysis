# Joint-scalar rho arithmetic closeout

The closeout compares complete target-charged `aG+bQ` restart work across
32 frozen secp256k1 targets. A generator-only-warmed OpenSSL arm now charges
its target `Q` setup and first joint multiplication. Fixed radix-81 and
mixed-76 charge their target Q tables, Horner evaluation, and affine output.
This closes the warmup boundary left open by the earlier one-point panel.

## Frozen inputs and source

The [fixture generator](make_rho_closeout_fixtures.py) uses a recorded
32-byte seed to create 32 Q points and 128 public `(a,b)` pairs per Q. The
manifest SHA-256 is
`f46ad43788b7f9241927904541cbeb03ea70a96ca95aa84d527a9b22ba8d12b8`.
The [independent affine verifier](verify_rho_closeout_fixtures.py) checked
all 32 Q points and all 4,096 expected `aG+bQ` points; its
[receipt](rho-closeout-fixtures/full-verification.json) records the full
scope. All scalar hex strings are 32 bytes, as required by the native
OpenSSL helper. Counts 1, 8, 32, and 128 use prefixes of each Q's same
scalar stream.

The [closeout overlay](native_rho_closeout_overlay.py) applies only after
the previous mixed-76 source bundle, SHA-256
`aa194966c8ce274f53b169c836baf16ff52c5d94ba384cec9994d72f65f02e8b`,
is reconstructed and checked. The [bundle builder](build_rho_closeout_bundle.py)
reproduced the closeout source bundle twice at SHA-256
`8f69f5c4f11d9a3b5d0771d1edef3cb5eca111e540f99e621bece5a98522ffd5`.
The local macOS ARM64 binary SHA-256 is
`fa5765521ecbfa51be525d715eaeddad4bba5fc9962d16e595519ec02b06a467`.
Every compiled Rust/Cargo source file matched the new bundle manifest.
The [native replay](rho-closeout-native-local-replay.json) checked 384
commands and 16,224 exact point outputs across all Q points, all four
counts, and the three modes. Its elapsed fields are local diagnostics.

The Linux x86-64 Pod rebuilt the frozen source with Rust/Cargo 1.93.1 and
OpenSSL 3.0.13. The benchmark binary SHA-256 is
`1ba810d3ad19b3c5153bf0345c736acec87a25d725aab9efffc4a55243c1202d`;
linked `libcrypto.so.3` is
`6866ed711dab8927e1bf82bf1cd30e828bdfc34f3cc1e83b1c9eb01ce6c37d9a`.
The allocation exposed an AMD EPYC 4564P, eight cgroup v1 CPUs, one NUMA
node, no CPU quota, and a 16-GB memory limit. The service ran on CPU 2;
measured children ran on CPU 8 or 24. The Pod did not prove physical-host
exclusivity, and its governor reported `powersave`. The
[source bundle](rho-closeout-evidence/source-bundle.tar.gz),
[allocation receipt](rho-closeout-evidence/allocation.json), and
[build log](rho-closeout-evidence/linux-build.log) are retained.

## One-restart Tier 1 selection

The [manifest generator](make_tier1_rho_closeout_panel.py) freezes 99 cases
per repetition: 32 Q points with direct OpenSSL/radix-81,
radix-81/mixed-76, and OpenSSL/mixed-76 pairs, plus three bracketing
OpenSSL A/A controls. Sixteen alternating repetitions give 1,584 pairs.
The first two comparisons are primary; the direct OpenSSL/mixed-76 pair is
secondary. Each case checks exactly the same public point. A/A ratios must
stay in `[0.90,1.11]`. The primary paired interval uses the median of each
Q's 16 log ratios, then a prespecified 10,000-draw cluster bootstrap over
the 32 Q points. Source, binary, fixture, linked `libcrypto`, host receipts,
raw arm order, and output points are checked by the
[independent auditor](analyze_tier1_rho_closeout.py).

The local manifest dry run generated all 99 cases and 1,584 planned pairs.
Its binary hash belongs to the macOS build and must be replaced with the
actual Linux binary hash before dispatch. A zero-pair raw dry run confirmed
that the auditor records all 48 missing A/A controls and leaves the Tier 1
gate false. The previous RunPod CPU Pod was observed `EXITED` on
2026-10-17. Its restart failed because its host lacked free memory. A
replacement 8-vCPU, 16-GB CPU Pod (`wfr1v86uyxt5q1`) was created, but its
assigned SSH port timed out despite a ready container and was stopped. The
next 8-vCPU, 16-GB CPU Pod (`lu2jj7z7kedvg5`) accepted SSH; its host receipt
and benchmark status are recorded in the run archives. Its Pod-scoped control
key accepted a stop request after the panels completed.

The [first CPU-8 archive](rho-closeout-evidence/one-cpu8/raw.tar.gz) and
[CPU-24 replication](rho-closeout-evidence/one-cpu24/raw.tar.gz) each contain
3,168 arms and 1,584 same-point pairs. The independent audits found no
structural errors or invalid arms. The CPU-8 run failed one OpenSSL A/A
control (ratio 0.822); CPU-24 failed four (0.860, 1.328, 0.561, 1.129).
Both aggregate speedup statuses therefore remain unknown. A preceding
[preflight rejection](rho-closeout-evidence/preflight-rejected.tar.gz), with
zero executed arms, is also retained: the first runner revision mistook its
housekeeping affinity for the Pod's full cgroup allocation.

| One restart, 32 Q points | CPU-8 descriptive paired ratio | CPU-24 descriptive paired ratio | Tier 1 status |
| --- | ---: | ---: | --- |
| OpenSSL globalwarm / radix-81 | 2.272 | 2.273 | Unknown: A/A gate failed in both runs |
| Radix-81 / mixed-76 | 1.048 | 1.048 | Unknown: A/A gate failed in both runs |
| OpenSSL globalwarm / mixed-76 | 2.422 | 2.425 | Unknown: A/A gate failed in both runs |

These ratios use the median paired log ratio within each Q, followed by the
median across 32 Q points. The full audits retain their cluster bootstrap
intervals and every A/A observation. The earlier single-Q OpenSSL `nowarm`
comparison reported 12.302x against mixed-76 under a different boundary;
charging only target-Q setup and evaluation after generator-only warmup
changes the descriptive ratio to about 2.4x here. The multi-Q radix-81 /
mixed-76 direction also differs from the earlier single-Q result, which is
why one exposed point cannot select the implementation.

## Reuse and worker decision

The separate [reuse panel](rho-closeout-evidence/reuse-cpu24/raw.tar.gz)
measured 1, 8, 32, and 128 restarts per Q with 32 Q points and eight
alternating repetitions, 6,336 arms and 3,168 pairs. Its
[auditor](analyze_tier1_rho_reuse.py) checked every exact output, source and
binary artifact, phase sum, and execution order. Counts 32 and 128 passed
their A/A controls; counts 1 and 8 failed two and one controls respectively.
Each retained-byte value below is the algorithm's reported G/Q table plus
scalar-plan allocation, not process peak RSS. OpenSSL reports zero retained
table bytes; this does not measure its internal allocation.

| Restarts per Q | OpenSSL median online ms | Radix-81 median online ms | Mixed-76 median online ms | Radix-81 / mixed-76 paired ratio, 95% Q-cluster interval | Gate |
| ---: | ---: | ---: | ---: | --- | --- |
| 1 | 0.219 | 0.095 | 0.090 | 1.047 [1.033, 1.079] | A/A failed |
| 8 | 1.655 | 0.530 | 0.540 | 0.983 [0.976, 0.989] | A/A failed |
| 32 | 6.852 | 1.971 | 1.925 | 1.029 [1.028, 1.032] | Tier 1 passed |
| 128 | 27.107 | 7.663 | 7.409 | 1.033 [1.031, 1.034] | Tier 1 passed |

At 32 restarts the target-preparation medians were 0.002, 0.350, and
0.446 ms for OpenSSL, radix-81, and mixed-76; corresponding restart
evaluation medians were 6.850, 1.622, and 1.480 ms. At 128 restarts,
mixed-76 reported 526,918 retained bytes versus 442,517 for radix-81.
The qualified 32- and 128-restart results locate a reuse regime where the
mixed-76 evaluation saving exceeds its preparation cost. They do not select
the one-restart worker path, whose separate A/A gate failed.

The collaborative rho phase profiler in the `crypto` repository records one
deterministic secp256k1 worker trace with 32 branch points,
four starts, and 10,152 walk steps. Its same-state local runs show large
wall-time variation, so its phase fractions are diagnostics. Its measured
per-step rate extrapolates to roughly 0.09% setup-plus-start time for 256
walkers with a 20-bit distinguished-point rule; that extrapolation must be
tested on the isolated runner. If setup and starts remain too small a
fraction, the worker experiment should direct effort to the walk addition.

Worker integration requires exact replay of branch points and walk states,
an explicit secp256k1 curve check, and a qualified paired throughput
improvement whose 95% lower bound exceeds 1.05 without unacceptable peak
memory growth. Otherwise the result closes as a measured arithmetic
finding with the default worker unchanged. The generic C rho path uses a
64-bit group order; the full-size target is the Rust collaborative worker.

The current decision is to leave the default worker unchanged. The
one-restart Tier 1 gate did not pass. The short deterministic worker trace
contains 32 branch constructions, four starts, and 10,152 walk additions;
its setup/start fraction varied widely under local contention. The longer
trace in [crypto PR #2137](https://github.com/aburan28/crypto/pull/2137)
independently replayed 32 starts and 106,327 walk steps. Its locally observed
setup/start share was 3.61%. A repaired-main replay of the same walk
transcript observed 7.01%; both are local diagnostics. The opt-in batch walk
lane in that PR matched serial ordered check-ins and work counts on all 32
frozen Q points at `dp_bits=12` and an 8,192-step
cap: 64/64 arms and 32/32 pairs completed. These receipts focus the next
qualified test on the walk addition. The frozen Tier 1 panel has 384 pairs,
including two A/A controls per Q and four repetitions. Default routing
changes only after its independent audit passes exact replay, host and
memory gates, and a Q-cluster 95% lower paired speedup bound above 1.05.

The worker branch has since been rebased onto repaired `crypto` main commit
`abee07ee7337d04a7e734333669ca1bacd6c763a`. The
[rebased-main validation receipt](https://github.com/aburan28/crypto/blob/ceddefda1ea16c99cb3b0cf3d3e8db4c9065f44f/experiments/rho-worker-phase-profile-20261017/rebased-main-validation.json)
pins that revision's source bundle rebuilt identically twice at SHA-256
`abd7a2eaeebca050dcf0a9f2290c02b116dbdd4b0bfb43cb45bf4be1ca5f7025`.
Its clean extraction built a byte-identical release benchmark and passed an
independent q00 serial/batch replay. On the complete checkout, 4,396 release
library tests passed with zero failures and 118 ignored; all 64 long replay
arms across the 32 frozen Q points matched in 32 serial/batch pairs. These
are build and correctness receipts, not qualified throughput evidence.

The current [shared-lock source receipt](https://github.com/aburan28/crypto/blob/3e3b055b6/experiments/rho-worker-phase-profile-20261017/shared-lock-source-validation.json)
pins the revised runner and auditor at source-bundle SHA-256
`ccc4c83128510e145bed6e8c04b26eb9a63f617bb2d3665826856ccd91902904`.
The bundle reproduced twice, built cleanly from extraction, and produced the
same binary; its q00 serial/batch outputs matched. The runner serializes
benchmark requests sharing the Pod's persistent queue root. A two-process
lock check passed, and the auditor rejects a container-local lock receipt.
This scope does not establish physical-host exclusivity.

The [repaired-main phase receipt](https://github.com/aburan28/crypto/blob/130890bec/experiments/rho-worker-phase-profile-20261017/rebased-main-phase-validation.json)
pins the current-source binary and transcript. On its local trace, a twofold
setup/start improvement would improve the profiled total by 1.036x, while
eliminating the phase would give an upper bound of 1.075x. The source and
timing conditions changed between the two traces; neither phase share can
bound the worker on a qualified host. The 768-arm worker panel remains the
decisive next test: exact replay, passing A/A and host-noise gates, both a
10% relative and a 64 MiB absolute cap on additional peak RSS, and a
Q-cluster 95% lower paired speedup bound above 1.05 are required to enable
batched routing. The Rust source transfer to RunPod was rejected by automatic
approval review, and the workspace lacks a rotated `RUNPOD_API_KEY` secret;
the hosted result is pending.
