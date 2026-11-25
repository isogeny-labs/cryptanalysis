# Hash-mixing comparison protocol

Written before timing. Use the frozen M31 auxiliary and plain public fixtures
and the same full Rust collector. Compare two compile-time hashes for the
contiguous 1,048,576-slot pair index. The control is the current SplitMix-style
finalizer. The candidate uses the top 20 bits of a single 64-bit multiplicative
hash. Keep capacity, probing, first-payload behavior, pair-row construction,
walk, elimination and answer checks identical. Use direct pair rows in both.

Compile two release binaries in isolated Cargo target directories. Run 24
matched blocks per basis, eight for each seed 0, 1 and 2, with 12 executions
of each hash first. Every timed arm regenerates its factor base, verifies its
identity against the frozen fixture, launches a fresh Rust process, checks the
expected public answer, and records parent-observed wall and parent-plus-child
CPU time. Validate matched pair equality for basis digest, trial count,
relation count, table size and answer. Preserve all failures and raw rows.

Host caches remain under system control; this is an exploratory local panel.
Compilation and fixture JSON loading are outside timing. Report per-basis
medians, paired ratios and wins. A narrower hash cost does not imply a solver
speedup unless the charged whole-run observation improves.
