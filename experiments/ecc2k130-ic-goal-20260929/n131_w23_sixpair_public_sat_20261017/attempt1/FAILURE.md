# Attempt 1: pre-solver assertion

The first frozen query built and wrote `ordinary.xcnf` (the saved 8.7 MB
formula), then stopped at `assert t3 - t0 < 20_000_000_000` in the frozen
runner. Its exit code was 1 and `query.stderr` has the traceback. The
solver was not launched; this is a pre-solver harness failure, not a
point-decomposition outcome. The original protocol, runner, formula and raw
logs are preserved here. The retry replaces the artificial 20-second
assertion with the declared 600-second target-dependent cap and uses its
own source-hashed protocol.
