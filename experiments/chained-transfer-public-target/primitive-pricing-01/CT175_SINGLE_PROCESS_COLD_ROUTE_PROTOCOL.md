# CT175 — prospective single-public-packet fresh-process transfer cost

Date: 2026-11-16 America/Denver (2026-11-17 UTC). Scientific standing: **[pcc:unverified]**. Source protocol committed before implementation. Companion to merged cryptanalysis #1692 and CT174; no new timing or whole-ECDLP claim.

## Defect isolated from CT174

CT174 `--paired-price` warms an entire process with **48 native parity replays, 144 forward route evaluations and 48 inverses** before collecting same-process ABBA and A/A samples. Those operations are outside its `same_process_setup_ns_decimal` (which times only `CheckedInstance::construct + Runtime::construct`). The existing output is useful as a **warm route diagnostic**, but its setup figure is **not** a cold-transfer full-cost estimate; including it without the preflight cost could undercount a cold attempt.

Do not change or reinterpret CT174's historical schema, frozen evidence, or the original CT125 norm-reuse evaluator. Add an explicit opt-in `ct172-replay --cold-route INDEX ARM` that starts a new process, takes exactly one of the 48 original public fixture rows, and evaluates **one** native CT125 route with no 48-row preflight, no inverse, no known-scalar reconstruction, and no unmeasured warmup. ARM must be exactly `direct_composite` or `strongest_retained_lift_chain`; INDEX is an unsigned decimal integer from 0 through 47. Reject extra CLI arguments, unknown routes, out-of-range values, malformed input or counter deviations.

## Cost boundaries and raw evidence

At the beginning of the program's `run`, start a monotonic in-process clock. Include JSON fixture parse and 48-row public-grid validation, then time the one actual `CheckedInstance::construct + Runtime::construct` (setup), and independently time `runtime.admit`, the *actual* CT125 route and `runtime.check_final`, on the same public packet. Confirm the full canonical 19-word output and all 21 actual counters against the frozen row **before marking the sample as accepted**. Capture end-to-end elapsed from start of `run` through successful verification, excluding final JSON serialization and OS loader/initial interpreter time. Explicitly label this `in_process`, not true externally timed cold wall, since OS process creation, dynamic loader, and final serialization are not included.

Emit a JSON `ct175-single-public-packet-cold-route/v1` record containing frozen index, direction/sector/public scalar *label only*, arm, verified 19-word output, checked counters, setup nanoseconds, native admission+route+final-check nanoseconds, end-to-end in-process nanoseconds, maximum resident set size if available, target architecture/OS and rustc version if executable exists. All elapsed nanoseconds must be decimal strings. No claimed CPU isolation, independent execution attestation, uncertainty interval or signed PCC.

External owner-admitted collector (separate future work) shall launch distinct subprocesses for A-B-B-A plus A/A on the *same* selected packet and fixed host, record full process wall/RSS/stdout/stderr/exit status for **every** invocation, and verify exact answers, counter vectors and distinct process IDs; run the full exceptional/generic 48 strata, preserve failed samples, host provenance, cold setup, sequence order and A/A drift. No script may synthesize measurements or run paid workloads by default. Never pool unequal cofactor/identity classes or treat a warm route measurement as cold.

## Decision rule

First establish actual native typecheck/link and exact output/counter parity on pinned sibling tree and owner-authenticated original artifacts. Then on approved matched hosts determine whether direct or retained **single-transfer** route costs less, including construction, startup and verification; log a loss as negative. Keep separate owner-admitted exact `C169,C13a,C13b,N2_actual,D_padd` primitive pricing, 695/701 independent custody, **complete single-target prime-field** rho/BSGS/index-calculus/transfer solver costs (including LA, inverses if used, setup and memory), uncertainty and signed PCC. No speed claim or scoreboard promotion follows from a transfer-only result.

The original STOP for paid EKS/Spot/GPU and authenticated original corpus/materialization requirements remain in effect. Do **not** run native workload through PR CI, launch paid compute, merge against required checks, or modify the original norm-point evaluator.

Sources checked: cryptanalysis `AGENTS.md`; merged #1692 CT172/CT174 Rust and protocols, CT173 audit, CT126 primitive pricing source; crypto #3877, #3904 and #4215; cryptanalysis #1523/#1533 and crypto #4178. Prior method: Gaudry–Hess–Smart (2002), *Constructive and Destructive Facets of Weil Descent on Elliptic Curves*, DOI 10.1007/s00145-001-0011-x (not evidence for a speedup). Shared research-KB MCP, exact S3 records, Rust/Cargo and original EKS admission unavailable in this runtime; no novelty or absence claim.
