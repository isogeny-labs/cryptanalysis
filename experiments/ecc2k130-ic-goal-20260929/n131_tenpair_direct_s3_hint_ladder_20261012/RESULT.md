# Four upper-tree hint cuts remain active on the N131 direct-S3 control

**Result.** Four frozen partial-information cuts of the direct-S3 ten-pair N131 circuit each reached a 60-second parent cap without a terminal SAT or UNSAT line. Every arm was given the constructed target choice, all ten true source selectors, and all ten true pair-output coordinates; only the upper-sum coordinates differed. Supplying the two highest nodes, the two middle nodes, all four bottom nodes, or the four higher nodes did not close the solver within its cap. The separately frozen all-eight-upper-node control returned SAT in 11.884 seconds with a complete literal-level model check. These capped arms identify the propagation boundary of this encoding under the exact constructed assignment; they do not exclude valid decompositions.

The [protocol](protocol.json) fixed the source and solver hashes, four node-index sets, one worker, 60-second parent cap per arm, and 4-GiB combined RSS cap before launch. The exact source is the previously checked [direct-S3 ten-pair circuit](../n131_tenpair_direct_s3_20261012/RESULT.md) over `GF(2)[t]/(t^131+t^13+t²+t+1)`, on the curve `y²+xy=x³+1`. It has ten free W18 seed-212 pair slots in its ordinary form. This panel supplies true fixture values only to locate a solver boundary and retains `candidate_id: null`.

The tree has leaves `0..9` and eight interior reciprocals in order: nodes `10..13` are the four disjoint bottom sums, `14..15` combine those into two four-pair sums, node `16` combines the first eight pairs, and node `17` adds pair nine before the final target link. The arm names below refer to indexes `0..7` in that interior list.

| Frozen arm | True upper indexes supplied | Added unit clauses including shared target, selector, and output pins | Terminal status | Solver wall | Sampled combined RSS | Restart rows |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| [Top two](top2.json) | `[6,7]` | 1,752 | `PARENT_TIME_CAP` | 60.009 s | 364,134,400 B | 784 |
| [Middle two](middle2.json) | `[4,5]` | 1,752 | `PARENT_TIME_CAP` | 60.036 s | 210,944,000 B | 333 |
| [Bottom four](bottom4.json) | `[0,1,2,3]` | 2,014 | `PARENT_TIME_CAP` | 60.014 s | 218,202,112 B | 279 |
| [Higher four](top4.json) | `[4,5,6,7]` | 2,014 | `PARENT_TIME_CAP` | 60.013 s | 233,193,472 B | 781 |

The shared [build receipt](build.json) records 6.457 s to reconstruct the exact circuit and 2.152 s to check its constructed assignment. Its raw XCNF matched the prior archived SHA-256 byte for byte before any solver arm began. Every arm was derived from that same formula, with only the listed unit clauses added. The [aggregate](aggregate.json) and [independent byte audit](audit.json) retain the terminal statuses, solver-log hashes, raw and gzip formula hashes, caps, and actual restarts. These CPU times are exploratory on an unisolated host.

The result directs the next experiment toward a target-derived joint condition that crosses more than one upper-tree cut, together with source-pair inversion. Pinning one local cut from a constructed fixture did not suffice under the frozen cap. Such a condition must be tested on an unpinned N41 public relation and projected to the N131 600-second/4-GiB search envelope before another ordinary public-point promotion. The remaining IC requirements are relation yield and rank, target descent and scalar replay, and the matched same-point rho comparison.
