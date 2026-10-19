# Historical radix-15 native panel lacks source provenance and process RSS

- **Status:** `open`
- **Kind:** source-provenance gap; empirical-evidence gap; implementation gap for a new reproducible native candidate
- **Affected work:** PR #907; [`15-position radix report`](../experiments/prime-j0-fifteen-position-radix-20261015/REPORT-2026-10-19.md); historical Tier 1 panel `2481bd3c0f7e491698694ccb039f1048`
- **Next action owner:** Native benchmark owner (unassigned); review owner for PR #907
- **Last updated:** 2026-10-19

## Problem

The historical 15-position versus 16-position native panel cannot meet the repository's exact-source and per-run memory-evidence criteria because its candidate parent source snapshot and every child process's peak RSS were not retained.

The affected configuration is the secp256k1 fixed-generator scalar recoding with Eisenstein radix `268−τ`, norm `71,023`, 15 positions, measured against the 16-position `190−τ` format on the 128-scalar frozen input set. The historical candidate overlay expects source SHA-256 `e195374c4e6fde368bdba106c769c6335cd319f9f5547e8e2291089fe055335e`; it produces source hash `aff42df465e44e2f3fe1d10c524b6a336a76c5091791894cac5cba618cc441ee` and recorded binary hash `979595ad1316aee2431f65cacb8ac1b71a70923d108cac3fafe6382a60d37cf9`. The run archive omits each child process's peak RSS. A container-wide cgroup peak does not meet either requirement. The original panel's acceptance criteria remain open even though its correctness, pairing, A/A, and repeat-bootstrap checks pass.

## Evidence and uncertainty

- **Observed:** [`REPORT-2026-10-19.md`](../experiments/prime-j0-fifteen-position-radix-20261015/REPORT-2026-10-19.md) records the 96 raw arms, 48 pairs, missing per-child RSS, the cgroup-wide peak, the required source hash, and the absent `/workspace/bench-sources` archive. `native268_overlay.py` checks the exact missing parent hash before modifying source. The manifest and summary retain the historical source and binary hash claims. A fresh review search found no source matching `e195374…`; available module snapshots have different SHA-256 values.
- **Observed:** The frozen input is recoverable: `experiments/prime-j0-mixed640-materialized-tree-20261013/selective-holdout.json` hashes to `7f4672b7b676969fe40056d0f14c6ecf45ad36109870cdf3466ebafd9e7b22d8`, matching the historical fixture. `group-replay268.json` and `screen268.json` retain independent output fingerprints. A new [`NATIVE_RECONSTRUCTION_PROTOCOL-v1.md`](../experiments/prime-j0-fifteen-position-radix-20261015/NATIVE_RECONSTRUCTION_PROTOCOL-v1.md) pins a recoverable Rust source snapshot and defines a separate future port/replay path.
- **Derived or proved:** A future build from the recovered source would be a new implementation snapshot. It cannot establish that the missing historical source or executable was reproduced, nor recover the absent per-process RSS values.
- **Suspected explanation:** The benchmark source and build tree were kept outside the repository under `/workspace/bench-sources` and were not included in the run archive. The reason those files were not retained is unknown.
- **Missing capability:** The exact historical parent source snapshot and child-process RSS records are absent. The recovered Rust base does not contain the historical overlay's split-prime section, so a new reviewed port is needed before a fresh native run.
- **What this evidence does not establish:** Missing artifacts do not show that the historical code or run was invalid; they prevent independent reproduction of that exact build and full memory-evidence compliance. The new protocol is not run evidence and does not replace the historical panel.

## What would unblock it

To recover the **historical** panel's original acceptance criteria, locate a source archive whose content matches `e195374…`, reproduce its overlay and executable hashes, and recover raw per-child RSS receipts for all arms. A new run from different source cannot satisfy these historical criteria.

- [ ] Recover the exact historical source and verify the `e195374…`, `aff42df…`, and `979595…` source/overlay/binary fingerprints from the archived build.
- [ ] Recover the historical per-child peak RSS for every measured arm, with process/arm identity and units.

If those records are permanently unavailable, use the versioned [`radix15-rebuild-v1 protocol`](../experiments/prime-j0-fifteen-position-radix-20261015/NATIVE_RECONSTRUCTION_PROTOCOL-v1.md) to create a new candidate snapshot, verify frozen outputs, and—only after separately pinning a reproducible 16-position reference—run a fresh paired panel with per-process RSS. That can establish results for the new implementation; it cannot resolve the historical panel's missing provenance.

## Next discriminating step

- **Action or proof obligation:** An owner with access to the original build archive checks for the exact `e195374…` source snapshot and raw per-child RSS receipts; otherwise, implement the separately versioned `radix15-rebuild-v1` port from the protocol.
- **Inputs and controls:** Historical source and binary hashes in the report/manifest; frozen fixture SHA-256 `7f4672b7…`; output fingerprints in `group-replay268.json`, `screen268.json`, and `linux-preflight.stdout`; a separately pinned radix-16 reference for any new performance panel.
- **Execution limits and stop condition:** No timing or paid/cloud execution is authorized by this record. The current step is artifact discovery and protocol preparation. For a future panel, stop before timing if exact source/fixture hashes, correctness outputs, reference identity, or per-process RSS capture cannot be verified.
- **Outcomes and next actions:** Matching original source and raw RSS would permit an exact historical reproducibility audit. A new source port that matches frozen outputs permits consideration of a distinct future panel only after the reference and all receipt requirements are satisfied. Missing original artifacts keep the historical claim qualified. Failed output checks stop the new candidate.
- **Recheck trigger:** Discovery of an archive matching `e195374…`, raw RSS records, completion of the versioned port, or review of a proposed new panel.

## Resolution and history

2026-10-19: Review repeated the local source-artifact search and confirmed the original snapshot and child RSS remain unavailable. Added `NATIVE_RECONSTRUCTION_PROTOCOL-v1.md` using the recoverable base commit and verified fixture/output fingerprints. No benchmark was run; the historical blocker remains unresolved.
