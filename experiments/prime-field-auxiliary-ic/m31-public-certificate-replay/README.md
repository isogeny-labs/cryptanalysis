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
