# Public M31 certificate replay

The comparison verifier checks each recorded relation individually against its two public base points. Across 455 rows of auxiliary seed 0, profiling the archived audit counted 911 scalar multiplications, 43232 calls to curve addition and 41867 calls to Python pow. Constructing five-bit position tables for each public base reduced this to 7992 curve additions and 6627 pow calls. The tables are allocated on each fresh curve instance and discarded at the end of that certificate. The verifier still uses the archived affine addition law, relation checks, and dependency checks.

From this directory run `python3 replay.py --compare --repetitions 7` with SymPy installed and the snapshot comparison data present. An extracted snapshot can be selected with `--snapshot PATH`. The frozen benchmark sources and data for this run were read from commit f9c7b49e7. Each row gives median complete audit time in milliseconds on an Apple M4 Pro, Python 3.13, with alternating execution order, fresh arithmetic tables, and warmed filesystem cache. Input reads, JSON decoding, setup and all arithmetic checks are timed. Interpreter startup and module imports are outside the timer.

| Arm | Seed | Archived verifier (ms) | Five-bit verifier (ms) |
|---|---:|---:|---:|
| Auxiliary | 0 | 45.963 | 7.927 |
| Auxiliary | 1 | 45.069 | 7.946 |
| Auxiliary | 2 | 45.037 | 7.838 |
| Plain | 0 | 43.204 | 7.608 |
| Plain | 1 | 44.710 | 7.872 |
| Plain | 2 | 44.831 | 7.883 |

Both paths rejected a copy of auxiliary seed 0 with the first relation's public scalar a incremented by one. Direct products agreed on the public generator and the identity at scalars 0, 1, 16, 31, 32, 33, 1023, 1024, 2^31−1 and 2^65+7. The theorem in Window.lean proves the radix-32 reconstruction step for an arbitrary additive commutative monoid. Run `lake env lean /absolute/path/to/Window.lean` in the project mathlib environment. The Python table implementation is validated by execution.

This is standard fixed-base arithmetic applied to independent verification. The archived benchmark records solver timing before it invokes the audit, so the measured gain contributes zero to its published collector timing.

## Same-target rho control and clock boundaries

Running `python3 control_audit.py` (or specifying the extracted snapshot with `--snapshot`) checks the public curve, order and both points for all nine archived M31 cases, replays each certificate using the original audit, and reads the decimal timings. The rho inputs have zero representatives. Each IC arm has 500.

| Seed | Rho solver (ms) | Auxiliary setup + solver (ms) | Plain setup + solver (ms) |
|---:|---:|---:|---:|
| 0 | 4.611 | 624.969 | 544.512 |
| 1 | 4.666 | 571.586 | 572.513 |
| 2 | 20.097 | 553.312 | 590.425 |

The slowest recorded rho time was 20.0969 ms. Even the fastest pair phase (60.104 ms) was 2.991 times that control. The fastest search phase (435.119 ms) was 21.651 times it. Both comparisons use the most favorable extrema across seeds and arms. An improvement that zeroes only one phase still leaves the other above every observed rho time. PhaseFloor.lean proves the inequalities on the recorded decimal bounds. The separate control replay binds those bounds to the archived files.

The IC pair timer includes header validation, input reads and pair-table construction. The reported search time is a residual after subtracting the pair and elimination phases. Rho's internal timer also starts before input reads and includes its walk-table setup. Both internal timers end before metrics serialization and independent auditing. IC's separately measured input setup is charged once to every cold run. The archived comparison/benchmark.py loops over auxiliary and plain only. Rho timings come from the retained per-seed rho files, so this comparison establishes target identity and recorded costs. Same-allocation interleaving, contemporaneous clock conditions and fresh wall-clock performance are unverified.
