# CT180 — prospective cold-time nesting audit

Date: 2026-11-17 UTC. Scope: **source-only consistency guard** on CT179's already frozen 48-packet/2,304-process transfer panel. [pcc:unverified]

## Source-of-truth time intervals

Read the committed CT175 Rust `ct172-replay/src/main.rs`: `started_in_process = Instant::now()` begins before fixture validation and `CheckedInstance::construct`; `setup_ns` records `CheckedInstance::construct` plus `Runtime::construct`; `sample_route` records admitted public transfer and `check_final`; `total_ns` is read after `sample_route`. Thus the same Rust monotonic clock measures disjoint setup and route intervals enclosed by its total. CT176 Python `run_sample` measures `time.perf_counter_ns()` around the complete fresh subprocess from before `Popen` through exit and capture, enclosing the child process execution.

For each accepted sample, in addition to previous exact outputs/counters and positive external time, require:

```text
0 <= setup_ns
0 < route_ns
0 < internal_total_ns
setup_ns + route_ns <= internal_total_ns <= external_process_wall_ns
```

The right inequality assumes elapsed-duration comparability of the two monotonic clocks on the declared host. If a platform violates it, refuse that panel and establish a separately admitted, measured clock-calibration protocol *before* changing the predicate; never silently clamp or impute. On Linux, both Rust `Instant` and Python `perf_counter_ns` normally use monotonic wall-clock sources. These are **consistency checks**, not cryptographic authenticity; a coordinated forger can still invent consistent records and independent signed execution evidence is still needed.

## Falsification controls (source-only)

1. Positive unchanged synthetic packet and complete 2,304-row panel remain accepted as **synthetic only**.
2. Change external wall from 3,000,000ns to 1ns while preserving otherwise valid output and hash; reject impossible inner > outer wall time.
3. Change native total from 330ns to 200ns, while setup=110ns and route=120ns; reject disjoint intervals exceeding total.
4. Change route from 120ns to 340ns with total=330ns; reject enclosed route exceeding total.
5. Change native total to zero; reject invalid duration.

Use the inherited `test_ct179_panel_adjudicator.py` under normal and optimized Python via the existing source CI; no Rust compilation, child subprocess panels, EKS, Spot or GPU jobs.

This check must **not** be interpreted as a timing improvement or a completed ECDLP attack. The original full 695/701 custody and native cold pricing remain unexecuted and protected by current owner budget STOP. No changes to frozen arithmetic, PR #1708, original fixture, PCC, workflows, or historical artifacts.
