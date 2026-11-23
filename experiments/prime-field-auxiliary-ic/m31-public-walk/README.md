# Ordered auxiliary coordinate generation at M31

The level-wise native walk brings complete construction of the archived 500-point auxiliary basis to 0.882 and 0.892 ms in two local Apple M4 Pro processes. The earlier native-root plus homogeneous-validation path took 1.729 and 1.748 ms in the same panel. Every invocation regenerates the public coordinates, validates the chain, lifts the target coordinates, filters the results and builds the ordered Python point list. Loading the C library, process startup, serialization and post-timing reference checks are outside the clock.

For each current list of m points T+iG in order, append a translated copy shifted by mG. This produces T+iG for 0 ≤ i < 2m in the same order as the serial walk. Double the stride for the next level. For this fixed public fixture ten levels produce the 1,024 required abscissas. Each level uses the archived batch-addition routine, which shares an inversion for the generic additions in that level. Stride doublings and closure checking have their own cost. Walk.lean proves ordered list equality for every level in an additive commutative group.

| Complete setup arm | First process median ms | Second process median ms |
|---|---:|---:|
| Archived Python setup | 10.7655 | 10.6132 |
| Native lifts, homogeneous checks, Python serial walk | 1.7292 | 1.7477 |
| Same setup, native serial walk | 0.9355 | 0.9861 |
| Same setup, native level-wise walk | 0.8816 | 0.8917 |

Medians of paired block ratios, first and second process respectively, were 12.384× and 11.905× against the archived setup, 1.995× and 1.993× against the previous implementation, and 1.096× and 1.113× against native serial. The level-wise path beat native serial in 20/24 and 23/24 blocks. Each process uses 24 four-arm blocks with balanced positions. These measurements apply to public preparation. They do not measure the subsequent relation search.

Run `python3 panel.py` with SymPy, a C++17 compiler and the sibling ABI and projective-check experiments available. The program retrieves the pinned group arithmetic and generator from Git. All 1,024 ordered coordinates and chain metadata are compared with the original before timing. The native paths check all points on the public auxiliary curve, return the actual successor of the last point for the original closure assertion, and retain coordinate uniqueness and every terminal chain check. Each timed result is compared with all 500 archived point pairs. The native fixture adapter is specialized to the full 1,024-point walk on y²=x³+x over M31.

Replay the ordering theorem with `lake env lean /absolute/path/to/Walk.lean` in the project mathlib environment. The theorem concerns the schedule, and the independent archived Python group implementation checks the native output.
