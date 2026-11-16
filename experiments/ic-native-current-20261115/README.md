# Current-upstream IC integration

This branch carries signed rational individual-log reconstruction and exact
forest reduction onto upstream `2b97ddf662`. It retains current inverse-based
smoothness tests, compact relation storage, durable collection journals and
the existing optimized/threaded modular solver. Its scope is the native
multiplicative-group implementation. [pcc:unverified]

The producer's ARM64 CTest log reports 21/21 tests passing, including the new
`ic_projection` test. That test checks rational reconstruction identities and
exhaustively compares projected graph solution sets. This is a producer
observation with no signed independent verdict. [pcc:unverified]

`PROTOCOL.md` freezes the current baseline, fresh public point law, one-target
first-call timer, optional repeat diagnostics, same-point rho controls,
placement/noise gates and bounded CUDA-host allocation before measurement.
`run.py` rebuilds on that host, retains all arms and replays returned scalars
using Python integer arithmetic. Tier-qualified fields remain null when a
gate fails. [pcc:unverified]

The earlier branch's measurements are archived in
`/Volumes/SSD990/cryptanalysis/experiments/ic-native-linalg-20261115/` and
identify their older baseline. A current-baseline measurement remains pending;
the earlier ratios are not carried into this comparison. [pcc:unverified]

The first CUDA-host allocation produced a native GNU 13.3 x86-64 build whose
CTest log reports 22/22 checks passing, including the ISA check and
projection/reconstruction test. Benchmark-wrapper compilation then stopped
before any timing input was run: strict C11 needed the POSIX clock feature
macro. The wrapper now declares that macro, and each retry selects a fresh
output directory through `IC_RUN_ID`. [pcc:unverified]

`launch-001` retains the pre-allocation missing-image-file failure;
`launch-002` and `run-001` retain the x86 build/unit logs, allocation status
and wrapper compiler failure. Both attempts have separate invalid benchmark
records; neither supplies a timing ratio. [pcc:unverified]

Requirement status: current-upstream port implemented with producer ARM64
and x86-64 unit checks; held-out timing panel pending; signed independent
claim standing and broader elliptic-curve/GPU optimization remain open.

Claim record: `PCC-20261116-188c73` (statement, unverified). This record does
not assert execution verification. Native log and remote raw outputs are
retained through the artifact/checkpoint tools, with per-run directories.
