# Lossless pair folding on the archived M31 coordinates

The domain is the 32 distinct structured roots in the archived depth-five public fixture at revision efb9330c1. Seventeen coordinates have a lift to the curve. A hash identifies two coordinates exchanged by a single projective involution and stores one lift bit per occupied orbit. Each pair with matching labels saves one label slot. Each pair with different labels forces one error when both coordinates share a prediction. The count of occupied orbits excludes keys, addressing and any metadata needed to compute the hash.

All 496 unordered pairs have distinct sums modulo p. An affine reflection identifies a pair exactly when its sum equals twice the center. Across all p centers, 241 merge one equal-label pair, 255 merge one mixed pair, and the other 2,147,483,151 give 32 distinct slots.

## Projective involutions

A nonscalar two-by-two matrix whose square is scalar has trace zero. If its lower left entry is zero, its fractional-linear action is an affine reflection. Otherwise normalize the matrix so its lower left entry is one. Its action takes x to (ax+b)/(x−a), with a²+b nonzero. Its pole and infinity form one orbit and the fixture contains only finite coordinates. For two distinct finite coordinates x and y the pair condition is xy = a(x+y)+b. Thus each unordered pair gives a point with coordinates (sum, product) in a plane. Two distinct pairs determine at most one line of this form because their sums differ.

The Python replay enumerates every disjoint pair of pairs, reconstructs the line, and groups coincident lines. A nonsingular involution is one-to-one, so any map with two or more merged pairs is found. The Lean check fixes one reference pair, discards singular candidates and inversion, and verifies that the remaining slopes to other pairs are distinct. Three merged pairs would repeat a slope. The executable checks on the archived finite list use native_decide.

| Merged pairs | Conflicting pairs | Nonaffine maps |
|---:|---:|---:|
| 2 | 0 | 25,479 |
| 2 | 1 | 53,742 |
| 2 | 2 | 28,539 |
| 16 | 7 | 1 |

Inversion x ↦ 1/x is the unique map with three or more pairs. Its 16 slots misclassify seven coordinates. The minimum lossless slot count is 30. One witness has a = 720732407 and b = 1078219647. It merges (3, 308768278) and (1213058799, 1685732321). The table includes only nonaffine maps with at least two merged pairs.

Replay the count with `python3 fixture_hash.py`. The script loads the pinned fixture, recomputes all lift labels by the quadratic character, compares the positives against the archived factor base, and checks the exact root list in FixtureHash.lean. The histogram is a Python enumeration. The Lean proof separately certifies the uniform pair bounds and the two witness counts. Run `lake env sh /absolute/path/to/replay.sh` using the mathlib environment in README.md. These are bounds on this fixture's label slots. A runtime improvement would require a separate measurement charging the cost of the projective key.

## Correcting inversion with coordinate parity

The original list already places each coordinate from positions 0–15 opposite its reciprocal in positions 16–31. Store one corrected label per pair, with bit i of 0x84c3 assigned to pair i in that order. To recover the label, XOR the stored bit with the parity of canonical coordinate bits 7, 12, 18 and 22 (least significant bit is zero). This classifies all 32 inputs exactly. The fixed mask is 0x441080. It is a parameter of this fixture.

For the mask search, encode a coordinate bit as a 16-bit vector whose ith entry is the XOR of that bit at the two members of pair i. A correction works precisely when its vectors XOR to the vector of observed lift-label differences. Exhaustive search through weight four gives two minimum masks, {7, 12, 18, 22} and {17, 21, 27, 30}. Lean checks the first decoder at every position, the reciprocal layout, and exclusion of all triples of bit signatures including a zero column for padding. A constant term cancels within a pair.

The decoder uses 16 orbit label bits when the mask is fixed in code and the orbit slot is known. A separately stored 31-bit mask plus these labels occupies 47 bits, exceeding the direct 32-bit label table. Arbitrary coordinates still require domain membership and an orbit-slot lookup. There is no measured wall-time improvement.

## Native decoder timing

On the local M4 Pro, the direct 32-bit label table took a median 0.0904 ns per label and the corrected 16-bit table took 0.1664 ns. The median paired corrected/direct time ratio was 1.827. Both paths expand labels to output bytes in a stream whose original fixture slots are supplied. These are throughput measurements over many queries. Each of 16 paired rounds runs both decoders on the same 65,536 pre-generated queries 128 times and alternates arm order. Round −1 warms both arms. The compiler barrier requires the byte output to be materialized for each repetition. Every arm's complete output is verified after timing. Setup, orbit-slot lookup, and arbitrary-coordinate membership are outside the timer. This isolates decoder cost for resident fixture inputs on one host.

Compile with Apple Clang 21 using `clang -O3 -mcpu=native -std=gnu11 fixture_decode.c -o /tmp/m31-fixture-decode`. Run `python3 fixture_hash.py --decode-input | /tmp/m31-fixture-decode` from this directory. Arm 0 is direct and arm 1 is corrected. Raw observations are in fixture_decode.csv.
