# `volcano --jobs`: historical timing observation

## Status

The pull request description reports wall times of 0.205 s and 0.101 s for
36 solves on a 33-bit prime-order curve, using four cores, before and after
adding `--jobs`. These are preserved as historical observations only. They do
not establish a reproducible or tier-qualified speedup.

## Evidence available

- Workload summary in the PR description: one 33-bit prime-order curve, 36
  solves, four cores.
- Reported wall times: serial 0.205 s; parallel 0.101 s.
- The PR source implements parallel execution of independent `(trial, arm)`
  solves and its correctness smoke test checks operation-count parity across
  job counts.

The PR description does not identify the exact command and arguments, curve
parameters or seed, reference and candidate source revisions, hardware model,
OS, compiler and build flags, allocation or isolation tier, paired run order,
sample count, per-run raw times, failed runs, or resource and throttling
receipts. It also does not retain the benchmark output or an independent
correctness receipt for those timed runs. The two values therefore cannot be
replayed or checked against the repository's CPU timing gates.

## What remains to validate the comparison

Run both variants on the same frozen curve and solve workload under an
applicable protocol in `docs/ISOLATED_BENCHMARKS.md`. Preserve the exact
commands, code and workload hashes, hardware/allocation receipt, isolation
preflight, alternating paired raw times, failures, resource counters and
correctness results. Include enough paired rounds to meet that protocol's
noise and uncertainty gates. Then update the performance index and any
affected rendered graph from those retained records. Do not overwrite this
historical note; give the new run its own report.

No performance graph was updated: the available two-number summary has no
paired raw observations or uncertainty, so it cannot be plotted as a verified
comparison. The change does not alter any isogeny or cryptanalytic-result
graph source.

## Current requirement status

The PR's deterministic operation-count parity is verified by
`scripts/cli_smoke.sh`. The parallel implementation's speed and tier-qualified
performance remain unverified pending the measurement above.
