# N131 W18 full-bin sparse product-space scan

The N131 W18 first four-atom block admits a complete native product-fiber
scan within the frozen one-worker envelope. The worker tested **32,947
usable first products** against the full `2^17` second-product space,
represented by 18 linearized-polynomial coefficients. It found one
degree-one GCD. A separate checked-Sage audit decoded that root to the
usable masks `(17,18)`, matched the first masks `(3,4)`, and re-evaluated
the four-atom resultant at the constructed block coordinate. The
[terminal verifier](terminal_verification.json) binds source and binary
hashes, raw logs, caps, native output, and the independent replay.

The source-law bridge used a separate GF(2^131) implementation over
`t^131+t^13+t²+t+1`. It checked the four pair equations, two four-atom
resultants, and three upper addition equations of the frozen constructed
four-pair witness. The exact usable pair counts for its seeds `7,3,5,1`
are **32,947, 32,916, 32,827, and 32,842**. Each full product space has
dimension 17. The [bridge result](result.json) and
[native audit](native_audit.json) retain the exact masks, rotations,
intermediate reciprocal coordinates, and input hashes.

| Phase or resource | Recorded value |
| --- | ---: |
| Full first-product scan | 32,947 / 32,947 processed |
| Full second-product space | 131,072 elements, sparse linearized representation |
| Native setup wall | 0.027456500 s |
| Native query wall | 29.429680208 s |
| Parent wall | 29.712894541 s |
| Sampled native CPU | 7.517875248 s |
| Native peak RSS | 4,997,120 B |
| GCD hits | 1 degree-one polynomial; decoded usable product |
| Terminal status | `COMPLETE_ALGEBRAIC_SCAN`, independently replayed |

The [native protocol](native_protocol.json) froze the exact input, support
table, source, header, compiled binary, compiler version, one worker,
600-second query cap, 610-second parent cap, and 4-GiB RSS cap. The
binary was built locally with `clang++ -O3 -std=c++20 -Wall -Wextra`;
the checked Sage launcher and saved runtime receipt were used for the
independent decoder. The host was contended, as the sampled CPU and wall
times show, so this is an exact stage-cost observation without an isolated
timing ratio. The query's supplied four-atom coordinate came from the
constructed correctness fixture, while the overall goal's ordinary
public target is a separate frozen workload.

The [proof map](PROOF_MAP.md) links the checked Lean composition and
source-filter theorems and states the remaining concrete formalization
bridges. The next target-conditioned gate is to derive the right-block
coordinates from a left partial sum and public target, then test the
complete right W18 source family and replay the result. The subsequent
ordinary-public-point search must bound left-family generation and all
failed probes inside the 600-second/4-GiB one-target interval.
