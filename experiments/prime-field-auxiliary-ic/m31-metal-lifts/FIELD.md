# Setup-charged full-field lift census

Each arm visits every canonical coordinate of the M31 curve y²=x³+2x+14, tests the lift label, and reports the number of visited coordinates, the number of lifts, the XOR of their x-coordinates, and the number of lifts with bit 2 clear. The previously published independent square-bitmap enumeration in ../m31-boolean-lifts/xor_period.c supplies the expected aggregates. No per-coordinate label array is requested as output. This differs from the streamed-array benchmark.

Build using bash build.sh /tmp/m31-field field. Run /tmp/m31-field 1 (GPU first) and /tmp/m31-field 0 (CPU first) in this directory. The CPU arm is a single host thread with the existing fused signed NEON kernel, generating its input and processing the ordered labels in 65,536-word chunks. Its partial final chunk uses the kernel's tail handling. The GPU arm generates coordinates in registers. It dispatches 32 batches of up to 2^26 coordinates using 65,536 workers. Each of 256 threadgroups returns four partial aggregates in 16 bytes. The host merges 128 KiB of partial outputs per full scan. FieldCoverage.lean proves the batch/worker/iteration decomposition is unique on the canonical range.

The wall timer for each arm encloses input generation, working allocation, classification, reduction and return of totals. The GPU timer also includes device and queue discovery, shader-source read, runtime library and pipeline creation, and all waits. Device time sums command-buffer GPU timestamps. The OS shader cache may persist between processes. Both local M4 Pro processes checked all four totals; these are aggregate checks and the Lean coverage theorem concerns indexing. The separately replayed streamed label comparison checks the shared lift function per coordinate.

| Order | GPU wall (ms) | Single-thread NEON wall (ms) | CPU wall / GPU wall |
| --- | ---: | ---: | ---: |
| GPU first | 455.77 | 10272.77 | 22.54 |
| CPU first | 393.11 | 9430.20 | 23.99 |

A fresh run of the independent square-bitmap C implementation returned 1,073,752,646 liftable coordinates, XOR 1,602,806,244 and 536,874,593 liftable coordinates with bit 2 clear. PARI found zero roots of the curve cubic in the field and curve cardinality 2,147,505,293, giving the same lift count after removing the point at infinity and dividing by two. Replay the index theorem from the repository root with `lake env lean experiments/prime-field-auxiliary-ic/m31-metal-lifts/FieldCoverage.lean`.
