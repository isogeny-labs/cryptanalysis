# Historical comparison exposed same-run timing semantics

The fresh original IC native test passes, with all60attempts and fifteen public cases. The new cross-run CI phase incorrectly used the unchanged same-run auditor to compare full historical records: actual comparator101/no accepted output, driver1. Whole actual output, executable/source snapshots, full prepared libraries and panic inputs/output remain retained in scratch and listed in the complete inventory. [pcc:unverified]

An independent Rust whole structural comparison finds480literal differences. Its full per-path/value output is retained here. The differences have paths ending in report.phases[i].wall or report.stats[22][1]; that statistic is wall_total in the original records. No comparison policy is retroactively inferred as a pass. The same-run auditor source and both whole files remain unchanged. A separate explicit prospective cross-run contract is required before any new verifier/retry. [pcc:unverified]
