# Direct x-bit mapping for the 512 KiB M31 bitmap

The three-way screen followed `BITMAP_HASH_PROTOCOL.md` on the frozen public auxiliary and plain M31 fixtures. Each candidate marked and queried the same 2^22-bit bitmap: the existing multiplicative hash, high 22 x bits, or low 22 x bits. The complete sorted exact-index maps were byte-identical across all arms, with SHA-256 `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879` (auxiliary) and `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa` (plain). Every occupied x passed the bitmap marking audit. All 30 matched three-arm blocks agreed on basis digest, answer `123456789`, trials, relations and index entries. No arm failed or was censored.

| Basis | Mapping | Wall median ms | CPU median ms | Paired mul/candidate wall | Paired mul/candidate CPU | Wall wins | CPU wins |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | Multiply | 94.938 | 88.171 | 1.0000 | 1.0000 | — | — |
| Auxiliary | High bits | 83.828 | 78.689 | 1.0900 | 1.1388 | 13/15 | 14/15 |
| Auxiliary | Low bits | 86.739 | 77.224 | 1.1291 | 1.1556 | 12/15 | 13/15 |
| Plain | Multiply | 83.805 | 75.682 | 1.0000 | 1.0000 | — | — |
| Plain | High bits | 70.108 | 64.598 | 1.1472 | 1.1231 | 12/15 | 14/15 |
| Plain | Low bits | 73.726 | 64.106 | 1.0759 | 1.0993 | 11/15 | 12/15 |

Both direct mappings met the screen rule; high bits were selected for confirmation because their worse-basis wall ratio and wall-win count were stronger. The separately frozen `BITMAP_HASH_CONFIRM_PROTOCOL.md` compared only multiply and high bits in 48 new matched blocks (96 fresh-process arms). All maps, marking audits, workload identities and checked answers again agreed; no arm failed or was censored.

| Basis | Multiply wall median ms | High-bit wall median ms | Paired wall ratio | High-bit wall wins | Multiply CPU median ms | High-bit CPU median ms | Paired CPU ratio | High-bit CPU wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 99.104 | 84.687 | 1.1655 | 22/24 | 91.159 | 78.362 | 1.1494 | 23/24 |
| Plain | 82.933 | 70.737 | 1.1556 | 23/24 | 77.665 | 66.335 | 1.1471 | 23/24 |

Both panels charged basis generation, table and bitmap setup, relation collection, elimination, generator answer verification and process exit. Compilation, fixture JSON loading and complete map audit were outside the timer; OS caches were not flushed. The same x coordinate is used for marking and querying, so the direct address change cannot create a bitmap false negative for marked x values; the exact index still decides membership. This is a local implementation gain on two frozen bases sharing one public target, pending independent signed performance verification. It is not an asymptotic change or a new mathematical algorithm. [pcc:unverified]

Raw CSV SHA-256: screen `da983df2f274c74f80ef9826a86391628ee808178efe7420a8b896b4d66cd2c1`; confirmation `2727dbdf66c8a6f107e2315132c7058921c3ec44aba2f7a927dba84ec0cfb633`.
