# Current-baseline native IC host-control report

The producer panel completed on a Modal L4 allocation using the current-upstream
baseline, GNU 13.3 x86-64 code and a CPU-only kernel. Its controller reports
replaying all 5,000 returned scalars with Python modular exponentiation.
Every qualified timing result remains null: all 25 pairs lack the required
placement/cgroup evidence, and 13 A/A controls exceed the frozen noise bound.
[pcc:unverified]

Claim: PCC-20261116-040da5. The recompute/replay reports are unsigned producer
reports; no signed independent standing or execution verification is claimed.

## Observations and timing scope

| Modulus | Collector | Raw first-call median reference/candidate wall ratio | Five-point range | Raw setup median ratio |
| --- | --- | ---: | ---: | ---: |
| 2000000579 | linear sieve | 1.810 | 1.215–5.449 | 1.749 |
| 1099511627791 | linear sieve | 3.521 | 1.747–7.863 | 1.955 |
| 281474976710597 | linear sieve | 2.421 | 0.156–39.258 | 2.374 |
| 14636773816760213 | linear sieve | 1.866 | 0.209–14.420 | 3.741 |
| 2000000579 | random exponent | 2.559 | 2.057–6.302 | 1.259 |

These are exploratory arithmetic ratios from rejected timing pairs, not
qualified gains. Ratios below 1 remain in the data, including 0.156 for a
48-bit point and 0.209 for a 54-bit point. The first-call definition was frozen
before the five fresh fixture indices 10..14 were generated. Each primary
call handles one previously unseen public point after reusable setup. The
additional 99 solves of that same point are secondary diagnostics and their
means do not replace the primary interval. [pcc:unverified]

The earlier 16.3x/28.5x observations used an older implementation baseline and
means of repeated solves. They remain frozen historical producer reports in
the original worktree. They do not establish the current-baseline, first-call
result in this report. [pcc:unverified]

## Controls and retained failures

The current baseline is 2b97ddf662. Its optimized linalg.c and compact journal
format were retained. The port changes rational reconstruction, step-power
lookup and forest relation reduction. On the four linear-sieve cases, reported
Lanczos iterations changed from 186/500/1093/2158 to 49/144/304/566; the random
collector remained at 68. The native build/CTest log reports 22/22 passing
checks, including the reconstruction/projection and x86 ISA tests.
[pcc:unverified]

The panel requests four CPUs, 8 GiB, one L4 and a 900-second cap. The sandbox
finished with exit 0 after about 71 seconds. It reports x86-64 and GenuineIntel,
but its model-name field is unknown. The exposed affinity mask had 20 CPUs;
the controller selected CPU 0. No local NUMA node or anonymous-page placement
was available in the recorded receipt. /proc/self/cgroup reports cgroup v1;
the frozen reader captured v2 file locations, which were absent. Equivalent
v1 counter visibility is untested, so this gap cannot be attributed wholly
to provider restrictions. [pcc:unverified]

Strong-rho controls use prime-power Pohlig--Hellman, reusable small-factor
BSGS tables, and one single-target rho solve per large-prime digit. A separate
Bernstein--Lange control retains its setup and online intervals. They use the
same public point and their exact scalar/status/time rows are in pairs.json.
Their timing ratios are also unqualified. The precomputation reference is
faster than the candidate on several retained points. [pcc:unverified]

Two earlier attempts are retained: the missing CUDA-image mount stopped before
allocation, then a native x86 build passed all tests but wrapper compilation
stopped on missing POSIX clock feature declarations. No timing inputs ran in
those attempts. The wrapper fix and distinct output-directory setting are
committed; their records remain invalid. [pcc:unverified]

## Evidence and requirement status

- run-002/host.json: allocation, hardware, source/binary hashes and placement.
- run-002/arms.jsonl and pairs.json: every arm, individual solve, calibration,
  same-point reference and rejection reason; S3 digests are in .artifacts.json.
- run-002/summary.json: raw paired ratios and intervals, with every qualified
  field null. CMake and CTest logs are retained in the same directory.
- docs/ic-native-current-20261115/: unsigned scalar and arithmetic reports.
- benchmarks/records/20261116T0249Z-ic-native-current-modal-003.json indexes the
  rejected panel; the two earlier records preserve the launch/build failures.

Current-upstream integration and ARM64/x86-64 unit checks have producer evidence.
Controlled timing and signed independent standing remain open. Broader
elliptic-curve/GPU optimization remains open. The named qualification gap is
[tracked here](../../problems/native-ic-timing-qualification.md).

The next arithmetic experiment specializes rational numerator/denominator
smoothness to 32-bit words, with portable fallback and optional AVX2/NEON
scanning. Its correctness must match the existing 64-bit factorizer before a
new frozen timing panel. A prepared host or an equivalent v1-aware preflight
is still required for timing promotion. No allocation is left running.
