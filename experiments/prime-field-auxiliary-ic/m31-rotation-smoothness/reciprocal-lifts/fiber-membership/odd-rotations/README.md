# Odd rotations in direct orbit membership queries

An even positive representative is a power of two times an odd divisor.
The divisor has the same 31st-power orbit key in the M31 field and inherits
smoothness. OddOrbit.lean proves the resulting equivalence for every orbit
key and inclusive smoothness bound. The orbit-key characterization in
m31-rotation-smoothness/OrbitKey.lean identifies equal keys with rotations.

The odd method reads the 31-bit word twice as a single 62-bit window. Each
set bit selects a right rotation whose low bit is one. It stops at the first
smooth representative. The existing multiple method scans left rotations,
so the search order can differ even when both find an early hit.

On the archived five-level query, counts.json records 516 vs 963 calls to
the divisibility predicate at bound 89, and 527 vs 962 at 211. Both methods
returned the same full list of hits. The benchmark used the same divisibility
constant and rebuilt it and the fiber data on each call. It tested both bounds
and methods in 24 counterbalanced blocks with 16 queries per observation.
On the shared Apple M4 Pro the median paired wall-time ratios (all/odd)
were 1.114 and 1.156 at bounds 89 and 211. The odd method won 13 and 15 of
24 wall-time pairs respectively. Timing order and shared-host variability
matter at this scale. The exact work-count reduction is more reproducible.

Run python3 replay.py to check edge and seeded inputs against direct modular
rotation and reproduce the timing panel. Select the implementation using
query.py's --method odd option. Replay OddOrbit.lean in the Lean 4.34.1
mathlib environment. These are in-process public fiber coverage measurements.
