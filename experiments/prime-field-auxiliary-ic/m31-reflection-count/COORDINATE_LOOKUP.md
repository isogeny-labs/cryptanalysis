# Exact coordinate-only lookup on the archived M31 basis fixture

A query is a 32-bit word. The result is a byte with value 0 for absent, 1 for a listed coordinate without a lift, or 2 for a listed coordinate with a lift. The 32 coordinate and label inputs come from the pinned public fixture verified by fixture_hash.py. All lookup arms receive the coordinate alone. The conventional table and the perfect tables store a full coordinate and its lift bit packed into one 32-bit word. The reserved all-ones word denotes an empty slot. Comparing the recovered key rejects misses even when their hash collides with a fixture member.

The compact table uses the upper six bits of the wrapping 32-bit product 59649x, giving one probe into 256 bytes. Ascending odd multipliers starting at one require 29,825 trials to find 59649 on this fixture. Widening the index to eight bits gives a 1 KiB table and the same search succeeds on trial 25 with multiplier 49. CoordinateLookup.lean checks both layouts against FixtureHash.roots and liftBit, proves every index is in bounds, and proves that lookup returns a bit exactly for the archived key and its correct label. The proof quantifies over every 32-bit input. The native tests exercise the C implementation against a separate sequential reference. Lean uses native_decide for the closed fixture checks.

## Setup-charged batch cost

Two local Apple M4 Pro processes each compare ordinary linear probing against runtime construction of the wider perfect table. Each timed transaction starts with the labeled keys already in memory, initializes fresh table contents, inserts all 32 keys, and resolves one batch of mixed hits and misses. The perfect arm searches the odd multipliers anew inside every transaction. The ordinary arm uses the upper six product bits of multiplier 2654435761 and probes consecutive slots at 50% load. Storage is reused and process startup, file parsing, label generation and generation of the query corpus occur outside the clock. The reports measure repeated operations with warm operating-system and processor caches.

| Coordinates per build | Ordinary median ns, seeds 1 / 2 | Searched perfect median ns, seeds 1 / 2 | Median paired ordinary / perfect, seeds 1 / 2 |
|---:|---:|---:|---:|
| 32 | 54 / 52 | 325 / 324 | 0.17 / 0.16 |
| 128 | 166 / 147 | 354 / 355 | 0.47 / 0.42 |
| 512 | 664 / 695 | 477 / 477 | 1.39 / 1.45 |
| 2,048 | 2,688 / 2,844 | 969 / 953 | 2.77 / 3.00 |
| 8,192 | 11,625 / 11,813 | 2,875 / 2,875 | 4.04 / 4.13 |

Each seed uses twelve paired rounds after one warmup, reversing order across rounds. Each batch is a prefix of the same per-seed mixed corpus. The timer includes rebuilding for every repetition. Equal outputs are required after each timed arm. The first tested size with a win on both seeds was 512. The gap from 128 to 512 was not sampled.

## Resident table throughput

The five arms are sorted-key binary search, a four-query NEON scan over all keys, ordinary linear probing, the compact perfect table, and the wider perfect table. Each process times 15 balanced rotations after one warmup, with twelve repetitions of 16,384 queries per arm per round. All output words are checked after each arm. Modes are all hits, alternating hits and misses, and all misses. Half the misses are deliberately drawn to collide with a chosen occupied compact-table slot. The remaining misses are sampled and checked against the independent reference. The corpus is synthetic and cache-resident.

| Mode | Binary ns/query | NEON ns/query | Linear probing ns/query | Compact ns/query | Wider ns/query |
|---|---:|---:|---:|---:|---:|
| All hits | 5.17–5.19 | 2.63 | 1.54–1.56 | 0.295 | 0.300 |
| Alternating | 5.15–5.23 | 2.63–2.64 | 2.09–2.34 | 0.295 | 0.300 |
| All misses | 5.13–5.30 | 2.63–2.65 | 2.41–3.36 | 0.295–0.300 | 0.305–0.315 |

Values are medians for the two processes, shown as a range. Throughput includes input loads, classification and output byte stores. A separate one-process setup comparison measures build plus 32 known-key queries. Linear probing took 70 ns, the compact table with its known multiplier 24 ns, the compact table with search 390 µs, and the wider table with search 321 ns. The separate panels use different query distributions. The measurements establish lookup costs on this host. End-to-end collector impact requires a run through its normal entry point, including the actual lookup frequency, required output, input mix, and other phases.

## Replay

Run the following from this directory on an Arm Mac. The recorded build used Apple Clang 21.0.0. Arm numbers in the resident panel follow the order of the five columns above. In the setup panel arms 0, 1, 2 and 3 denote ordinary, compact with known multiplier, compact with search, and wider with search. In the charged panel arms 0 and 3 denote ordinary and wider with search. Raw records retain all warmups.

```sh
python3 fixture_hash.py --decode-input > /tmp/m31-coordinates.txt
clang -O3 -mcpu=native -std=gnu11 -Wall -Wextra -Werror coord_lookup.c -o /tmp/m31-coordinate-lookup
for seed in 1 2; do
    /tmp/m31-coordinate-lookup "$seed" < /tmp/m31-coordinates.txt
    /tmp/m31-coordinate-lookup --charged "$seed" < /tmp/m31-coordinates.txt
done
/tmp/m31-coordinate-lookup --setup < /tmp/m31-coordinates.txt
```

The directory's replay.sh rebuilds the Lean certificate from a fresh temporary module directory using the mathlib environment documented in README.md.
