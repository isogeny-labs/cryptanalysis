# Balanced nine-pair addition topology on the ECC2K-130 public point

The N131 W18 nine-pair decomposition circuit now has an eight-link balanced
addition tree with depth four, compared with depth eight in the prior serial
chain. It keeps all nine free pair selectors, the exact 18-distinct-folded-
column shield, and all 524 raw-fiber/Frobenius choices of the same public
point. The complete constructed assignment passes every clause and native
XOR row, and [the checked Lean theorem](PROOF_MAP.md) proves equality of the
balanced and serial nine-point sums under point-addition associativity. The
ordinary public-point query entered CryptoMiniSat search and reached its
frozen 600-second target-dependent cap with `BOUNDED_UNKNOWN`.

The exact curve is `y²+xy=x³+1` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, curve
`EC1N131Ckb1heb5f1998f20b`, subgroup order
`680564733841876926932320129493409985129`, and cofactor four. The
workload is `cc09e7eb202a`, with the public point and all source hashes in
the [frozen protocol](protocol.json). This is the previously published
point used by the [serial shield](../n131_w18_ninepair_orbit_shield_20261012/RESULT.md),
so the topology is isolated but the run is not an unseen-target test.

| Circuit measure | Serial shield | Balanced tree |
| --- | ---: | ---: |
| Addition dependency depth | 8 | 4 |
| Variables | 510,634 | 510,634 |
| AND gates | 221,160 | 221,160 |
| CNF clauses | 807,483 | 807,483 |
| Native-XOR rows | 286,693 | 286,693 |
| Free source codes per pair slot | 33,191 | 33,191 |
| Raw-fiber/Frobenius target choices | 524 | 524 |

The generated ordinary formula has SHA-256
`cf5829a127c56e7611d0a33077a38c72a3ca20527f6f1a15552444f4184ae674`.
The balanced tree changes intermediate sums, so its nonzero-coordinate
requirements can exclude a different exceptional set than the serial tree.
The shared pair source count remains an upper bound, not a measured yield
for this fixed point.

| Frozen ordinary-query phase | Charged wall |
| --- | ---: |
| Target orbit and four raw fibers | 0.168 s |
| Formula construction | 8.572 s |
| Formula serialization | 0.028 s |
| Solver search and stop | 591.291 s |
| Terminal parse | 0.001 s |
| **Target-dependent attempt total** | **600.061 s** |

The one-worker run used the same 600-second total cap, 4-GiB combined RSS
cap, solver binary, flags, target, and source policy as the serial shield.
Sampled parent-plus-solver peak RSS was 683,687,936 bytes. The solver wrote
2,151 actual `c rst` rows and no SAT/UNSAT status line; stderr was empty.
The parent killed it at the frozen total cap. The
[independent audit](audit_result.json) rebuilt the ordinary XCNF byte for
byte, matched the terminal logs and phase sum, and confirmed that search
began. The [archive receipt](archive_receipt.json) binds deterministic gzip
copies of both formulas to their uncompressed hashes and byte counts; replay
with `python3 -B ../n131_w18_ninepair_orbit_20261012/archive.py . --verify`.
The accepted Sage runtime receipt was captured before the measured query in
`sage_runtime_info.json`.

This result tests topology while holding the Boolean work count fixed.
The two capped ordinary searches do not establish a successful-cost ordering;
their CPU service and host contention differ, and no isolated-host timing
receipt is available. The next algorithmic gate is an exact target-derived
partial-sum proposal or rejection rule that preserves an ordinary N41
relation under independent replay, then an N131 query with the same frozen
source and resource envelope. `candidate_id` remains `null` until a complete
IC pipeline is specified and measured.
