# Integrated M31 bitmap lookup screen and validation

The integrated `PairIndex` now marks each constructed finite pair-sum x in a
128 KiB bitmap when the field is M31 and the factor base has at most 384
columns. A clear bit skips the exact HashMap lookup; a set bit still uses that
lookup and replays the original signed witness. Identity has its own slot.
This is a representation filter, not a change in relation probability or
search order. `Bloom.lean` in `m31-full-rust-comparison` establishes the
logical no-false-negative and first-payload premise for a marked bitmap; it
does not prove this Rust code, its cost, or any runtime property.

## Development screen on one frozen public target

The original all-sizes bitmap implementation ran against the exact HashMap
control on Q=(988441464,1643383878), B384 and B768, seeds 0–2. All 12
fresh-process arms solved and independently verified `[scalar]G=Q`; every
matched pair had identical basis points, scalar, full certificate, work and
pair counters. No failures or censored arms occurred. `bitmap-lookup-raw.csv`
records charged wall and parent-plus-child CPU, internal phases and report
hashes. [pcc:unverified]

| Basis | Control wall median ms | Bitmap wall median ms | Median paired control/bitmap wall | Control CPU median ms | Bitmap CPU median ms | Median paired control/bitmap CPU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B384 | 30.950 | 26.380 | 1.2050 | 30.042 | 25.760 | 1.1986 |
| B768 | 36.185 | 37.762 | 0.9582 | 35.249 | 36.462 | 0.9667 |

The frozen two-size acceptance gate failed at B768. The original all-sizes
binary SHA-256 was
`40f1b3de784229d75294f5779cb792afcc8891529cb78da75136e653993646fa`;
the control was
`7301092fd58bb502e14daef709595114467374312c306d8ebf6a57de0127f494`.
The original screen raw CSV SHA-256 was
`e77b24b4952a77cdc8d87dde213b704577430daefafb41dfc641fb351b2a6381`.
The failed B768 observation remains part of the record and led to the
size-limited amendment in `BITMAP_TUNED_PROTOCOL.md`.

## Size-limited validation on five prior public targets

After freezing `BITMAP_TUNED_PROTOCOL.md`, the thresholded candidate and
control ran on all five public targets from `fresh-public.json`, seeds 0–2,
along with matched archived C++ rho. All 75 arms solved and independently
verified their public group equations. Within every same-size pair, basis
points, scalar, full certificate, work and pair counters were identical.
There were no failed, censored or replacement arms. The B768 candidate is
the exact HashMap path and serves as an A/A control. The fifteen cells reuse
five independent target points. [pcc:unverified]

| Path | Median charged wall ms | Median charged CPU ms | Median internal cold ms | Median index build ms | Median online ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Control B384 | 32.446 | 32.081 | 28.380 | 2.934 | 24.989 |
| Bitmap B384 | 31.090 | 30.305 | 26.378 | 3.149 | 22.737 |
| Control B768 | 34.224 | 33.421 | 29.183 | 13.102 | 14.772 |
| Tuned B768 fallback | 34.361 | 33.784 | 29.599 | 12.841 | 15.419 |
| Matched rho | 11.243 | 10.772 | — | — | — |

| Paired ratio, numerator/denominator | Median wall | Wall wins for denominator | Median CPU | CPU wins for denominator |
| --- | ---: | ---: | ---: | ---: |
| Control B384 / bitmap B384 | 1.0616 | 14/15 | 1.0792 | 13/15 |
| Control B768 / tuned B768 | 0.9982 | 7/15 | 0.9943 | 6/15 |
| Control B768 / bitmap B384 | 1.0769 | 11/15 | 1.0734 | 11/15 |
| Rho / bitmap B384 | 0.4564 | 0/15 | 0.4435 | 0/15 |

Target-level median control/bitmap B384 wall ratios were 1.077, 1.026,
1.109, 1.077, 1.034; CPU ratios were 1.085, 1.039, 1.100, 1.079, 1.058.
Ratios are medians of paired ratios, not ratios of the displayed arm medians.
The B384 effect is a local constant-factor gain in the integrated full solve.
It does not close the matched rho gap, and the bitmap is not a new
mathematical algorithm. This panel uses one shared Apple M4 Pro host with
uncontrolled OS caches and background load; the B768 A/A cells quantify some
of that variation. [pcc:unverified]

Wall and parent-plus-child CPU start before process launch and end after exit,
JSON/metrics parsing and public group-equation verification. IC basis
generation, index build, online relation search, elimination, certificate
replay and teardown are charged. Compilation and reading the frozen fixture
file are excluded. Each process had a 20s deadline, none reached. The tuned
binary SHA-256 was
`e5f13b960f620e6aaae3c99ca17ee82963b4df981d89585688b8bbe9a35b4804`;
the source `pair_index.rs` SHA-256 was
`55ea706d9f769ca8f16e8131e2e9f152108dd7fb983a534f1258a16e2c604efc`.
`bitmap_tuned_replay.py` SHA-256 was
`7658f7516e81e7990c3af66b6bd8408583ef40156341d5e2a5aa1b9d804f6942`;
`bitmap-tuned-raw.csv` SHA-256 was
`de2f4550437ae7678c47649a8053bd076bb115ed98e46a57b783ffddc7ba9500`.
Per-process stdout, stderr and rho metrics remain local with digests in the
CSV; they are not asserted to be independently archived. [pcc:unverified]
