# Compact M31 public pair-table build

Run `python3 replay.py` to reproduce the comparison on a little-endian host.
The runner compiles the same pair builder twice at -O3. The control uses
`std::unordered_map`. The candidate uses 524,288 contiguous eight-byte slots
and linear probing. Both use the existing hash function, retain the first
payload for each key, and check every stored key and pair index against the
same independently regenerated, digest-checked Python reference after timing.

Each process starts with 500 public representatives of the curve with
coefficients (2,14). The clock covers signed expansion, allocation, curve
checks, batch additions and compact insertion. It excludes fixture generation,
verification, destruction and subsequent use of the table. Each basis has 24
paired rounds, with each implementation running first 12 times.

| Public basis | Node median (ms) | Flat median (ms) | Median paired node/flat | Flat wins |
| --- | ---: | ---: | ---: | ---: |
| Auxiliary | 23.51 | 10.65 | 2.096 | 24/24 |
| Plain | 23.81 | 10.40 | 2.074 | 24/24 |

The raw observations in replay.csv come from one local arm64 host with
Apple clang 21.0.0. Background work was active. The timings address this
construction phase only. The design changes allocation, collision handling
and slot density together, so the comparison estimates their combined effect.
