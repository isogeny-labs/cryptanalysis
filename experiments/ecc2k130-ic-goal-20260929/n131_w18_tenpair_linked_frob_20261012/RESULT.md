# Linked W18 pair slots on the frozen N131 public point

**Sharing the first two N131 pair-source selector and reciprocal wires yields a checked 18-column ten-pair circuit.** Its constructed witness passed the complete SAT assignment check and an independent Sage group replay. The ordinary query on the frozen public point ran for `600.103367458` seconds with one worker and peak sampled combined RSS `248266752` bytes; the recorded terminal status is `BOUNDED_UNKNOWN` at `TOTAL_QUERY_TIMEOUT`. The [byte-for-byte terminal audit](audit_result.json) rebuilt the public XCNF and checked the raw solver receipt. `candidate_id` remains `null` while the full IC pipeline is unresolved.

## Source and control

Slots 0 and 1 use the same 17-bit W18 source code and the same pair-output reciprocal, then apply rotations 0 and 16. The other eight slots retain the frozen rotations `32,48,64,80,96,112,128,8`. The exact conflict shield excludes cross-slot column overlaps except the intentional repetition between slots 0 and 1. The source consequently has nine free pair codes and 18 distinct folded columns. The public-query circuit links an x-coordinate quotient: it allows either sign of each pair point. A returned model requires independent signed group replay before it can be used as a relation.

The [protocol](protocol.json) was frozen before the [constructed control](control_result.json) and ordinary query. The constructed fixture uses the same signed pair point at slots 0 and 1, with Frobenius rotation 16 on slot 1. Its full SAT assignment check covered `522032` clauses and `80648` native XOR rows. The [checked Sage audit](sage_fixture_result.json) independently replayed every pair source, the linked signed points, the ten-point sum, the 18-column shield, and multiplication by four to the recorded subgroup point. [Sage runtime information](sage_runtime_info.json) was saved before that audit. The [proof and verification map](PROOF_MAP.md) identifies the exact mathematical and computational scope.

## Ordinary public query

The public target is `[1052727368764798954359115163823647684025, 2071227447786120917960296877345506689833]` on `EC1N131Ckb1heb5f1998f20b`, workload `cc09e7eb202a`, with 524 distinct raw-preimage/Frobenius reciprocal choices. The [query receipt](query_result.json) records all exclusive phases:

| Charged target-dependent phase | Nanoseconds |
| --- | ---: |
| Target orbit and fibers | 251,590,875 |
| Formula construction | 22,219,062,208 |
| Formula serialization | 286,905,834 |
| Solver search, including capped attempt | 577,337,389,583 |
| Terminal parse and decode | 8,418,958 |
| **Total** | **600,103,367,458** |

The parent killed the worker at `TOTAL_QUERY_TIMEOUT`; solver exit code was `-9`, and the raw log has no terminal SAT/UNSAT line. The [frozen terminal audit protocol](audit_protocol.json) binds the source, query receipt, raw solver logs, control, and ordinary formula. The [audit source](audit.py) reconstructed the ordinary formula byte for byte and verified the receipt and phase sum. Both XCNF files are preserved as deterministic gzip archives; the [archive receipt](archive_receipt.json) proves decompression reproduces the original hashes and byte counts. Restore an XCNF with `gzip -cd control.xcnf.gz > control.xcnf` or the corresponding `ordinary` filename before rerunning the terminal auditor.

| Structural diagnostic | Earlier ten-pair binary-Frobenius circuit | Linked circuit |
| --- | ---: | ---: |
| Variables | 258,801 | 256,011 |
| AND gates | 172,560 | 170,333 |
| CNF clauses | 528,856 | 522,044 |
| Native XOR rows | 81,074 | 80,659 |
| XCNF bytes | 16,141,734 | 15,801,197 |
| Public query status | `BOUNDED_UNKNOWN` at 588.5150735 s | `BOUNDED_UNKNOWN` at 600.103367458 s |

These counts compare the formulas on the same public point. The host was not isolated for a CPU timing comparison, and the solver's own reported time advanced more slowly than parent wall during this run. The status rows retain their exact caps and resources.

## Next algorithmic gate

The first two signed pair points in the constructed witness satisfy `P_1 = τ^16(P_0)`. Their sum's x coordinate is determined by the x coordinate of `P_0`, independent of the choice between `P_0` and `-P_0`. Replacing the first two leaves and their free sign branch with this exact unary prefix would enforce the intended signed linkage before the target equation and remove one pair-addition ambiguity. The next iteration must prove the characteristic-two identity, check it on the frozen source, implement the reduced circuit, pass an unpinned constructed control with independent group replay, and only then spend another capped ordinary query.
