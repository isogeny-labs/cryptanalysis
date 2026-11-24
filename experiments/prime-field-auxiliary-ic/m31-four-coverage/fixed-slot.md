# Fixed-slot membership on public M31 coordinates

At 256 queries for a new 17-key base, a freshly initialized 512-slot table beat the scan and ten-offset window in each of three processes on the disjoint confirmation panel. Both smaller and larger query batches favored an existing method. On this Apple M4 Pro, the result supports a batch-size-specific choice for public coordinate membership.

The fresh arm fills 512 32-bit words with the reserved value 2147483647, writes each full coordinate at its low nine bits, and records any overwrite. With a collision it scans the base for every query after paying the build cost. Otherwise it checks equality of the complete stored and query coordinates. The input domain is canonical residues strictly below the sentinel. SparseWindow.lean proves the collision-test criterion, membership including fallback, and complete reset after clearing touched slots. It models table writes functionally. The C++ timings are empirical.

## Disjoint confirmation

All figures are medians of ten measured rounds in ns/base after five warmups. Each traversal includes the entire construction, all 4,096 bases, and every fallback. Query generation and byte-for-byte checking against linear search occur outside the timer. About half the queries are sampled from the base. Memory and processor caches warm across traversals.

| Queries per base | Scan, range across processes | Ten-offset window | Fresh 256 slots | Fresh 512 slots |
|---:|---:|---:|---:|---:|
| 64 | 36.9–37.5 | 95.9–106.5 | 44.6–45.8 | 49.4–51.1 |
| 256 | 143.0–143.6 | 147.1–148.0 | 126.1–127.8 | 123.9–124.4 |
| 1024 | 569.8–610.1 | 325.1–333.7 | 441.3–454.0 | 403.8–417.8 |

## Replay and negative results

Compile window-cost.cpp with Apple Clang 21.0.0, -std=c++17 -O3 -mcpu=native -DM31_FIXED_PANEL. Use the original-order holdout keys from window-cost.md. Add the define in the table for that panel. Each CSV row in fixed-slot.csv has its process seed. With A arms there are A warmups and 2A measured rounds per cell.

| Seeds | Additional define | Input and comparison |
|---|---|---|
| 25–27 | none | Original holdout, 512 and 4096 slots initialized once per traversal and cleared at touched addresses after each base |
| 28–30 | M31_COLD_CONTROL | Original holdout, adds a fresh 4096-word table per base |
| 31–33 | M31_INDEX_CONTROL | Original holdout, adds a fresh 4096-byte index table with zero marking an empty slot and a checked coordinate load on occupancy |
| 34–36 | M31_SMALL_CONTROL | Original holdout, fresh 256- and 512-word tables versus scan, sort and window |
| 37–39 | M31_SMALL_CONTROL | Generator seed 291162, first 4096 bases, seven overlap original holdout |
| 40–42 | M31_SMALL_CONTROL | Same generator seed, first 4096 distinct bases excluding all original holdout bases |

The original window tried 3.394 offsets per base on average. The low nine bits alone separated 3157/4096 original bases, and the low twelve separated 3942/4096. The 4096-slot reused table won at 64 and 256 queries but lost to the window at 1024. Freshly initializing 4096 words or 4096 index bytes lost at 256. All results, including the overlapping panel, are retained.

To regenerate the disjoint input, use the sample.gp substitutions from window-cost.md with seed 291162 and count 4128. For each row retain the 17 coordinates whose indicator is one, in generator order. Compare sorted key tuples to detect duplicates against all 4096 original bases and all previously accepted rows. Stop at 4096 accepted rows. Write each row as decimal integers separated by single spaces and terminated by a newline. The resulting input SHA-256 is 06a6f57a005ba5d452ed0cf98aee85614a0d73ad559428e8154299b6b5f578fd.
