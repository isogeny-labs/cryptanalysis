# Exact target join for 1,620 N41 four-point families

An exact finite-root join reduced each target query from **2,624,400 ordered family-pair checks** to **25,920 target-conditioned root probes** for the frozen N41 W6 rotation-zero shared-seed source. The constructed eight-point control yielded **54 ordered family matches** satisfying eight distinct folded columns. The frozen public point yielded **zero** within this exact restricted family. An independent checked-Sage enumeration reproduced both counts and replayed the positive witness.

The [producer protocol](protocol.json) fixes curve `EC1N41Ckb1h7d5e80d3c4d0`, `GF(2)[t]/(t^41+t³+1)`, `y²+xy=x³+1`, 32 rational source masks, 26 folded columns, 1,620 eligible four-mask families, one worker, 120 seconds, and 4 GiB. The method is a proposal with `candidate_id: null`. It compares one constructed control with the previously frozen N41 public point; it does not sample a natural relation rate.

Each four-point family has eight distinct x roots after identifying global negation; both point lifts restore its sixteen signed outputs. The producer builds an index from x root to family IDs. For each left root point `P` and each sign, it computes `x(Q-P)` and looks up right families. This is exact: a right point has the queried x precisely when one of its two lifts can complete `P+R=Q`. The eight-column rule is checked on every hit. This avoids crossing the eight roots of every family pair, while retaining complete target-specific witnesses.

| Frozen target | Root probes | Ordered family hits | Hits with eight distinct columns | Left families with valid hit | Query wall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Constructed eight-point control | 25,920 | 54 | **54** | 18 | 19.441 s |
| Frozen public point | 25,920 | 0 | **0** | 0 | 19.123 s |

The [producer result](result.json) records 49.213 seconds for building the 12,960-root index and both queries, with 21,774,336 B peak RSS. The [independent Sage replay](sage_audit.json) reconstructed the field, curve, signed source points, all families, both targets, and the full target joins through separately implemented curve arithmetic. It completed its replay interval in 80.430 seconds with 212,631,552 B peak RSS. Each arithmetic interval stayed inside the frozen 120-second/4-GiB stage cap. The [checked runtime](sage_runtime_info.json) was recorded outside the replay interval; these CPU wall times are exploratory because the host was not isolated. The [terminal verifier](verification.json) binds code and inputs to both results and checks the stage caps.

The exact join is a useful **N41 finite-family baseline**, but its index requires enumerating every four-point output before the target query. The frozen public-point result is complete only for this W6 rotation-zero shared-seed family; other rotations and point-decomposition methods remain separate. For N131, the unresolved step is to reject implicit four-point families *before* their roots are enumerated. The next test should compose the upper S3 target equation with an implicit family representation on unpinned N41 controls, then measure complete failed-probe work and memory before N131 promotion.
