# Raw-preimage accounting correction for the N41 orbit report

The N131 gate paragraph in [the earlier N41 41-orbit report](../n41_sixpair_target_orbit_20261016/RESULT.md) gives an orbit-summed W23 mean near 1,052 while discussing a query over **one raw preimage**. That mean counts relation labels across **all four raw preimages** of each subgroup target. It is valid under that all-preimage input law; it is not the mean for the single-raw query used in the N41 experiment.

For a uniformly selected raw point `U` in the curve group of order `4r`, the exact labeled relation mean over its 131 Frobenius conjugates is one quarter of the all-preimage subgroup mean. The audited W23 signed-tuple bounds therefore give `[262.941389580040208…, 262.960186007758632…]` for that uniform-raw law. A frozen deterministic section choosing one raw preimage from each subgroup target need not have this mean; only the subgroup reach ceiling in `RESULT.md` applies to it without a further distribution proof.

The prior N41 search receipts, 41 Sage relation replays, rank, SAT cap, and factor-base census are unaffected. This dated note supersedes only the interpretation of that N131 mean. The exact rational values and source hashes are in [result.json](result.json) and [terminal.json](terminal.json).
