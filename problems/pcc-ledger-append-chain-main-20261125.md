# PCC append-chain on main repeats sequence numbers

- **Status:** `open`
- **Kind:** provenance and verification infrastructure failure
- **Affected work:** M31 bitmap theorem PCC project claim following PR #1960; draft PR #1978; any new PCC claim or signed standing that requires a valid `pcc/ledger.jsonl`
- **Next action owner:** repository owner or PCC ledger maintainer; this producer must not rewrite the append-only ledger
- **Last updated:** 2026-11-25

## Problem

The current `main` ledger has two divergent append histories joined into one file, so `pcc claim new` refuses to append and the M31 bitmap Lean theorem cannot acquire a new project-backed PCC claim or signed standing. The proof gate itself passes the pinned Lean project; the failure is in claim custody.

## Evidence and uncertainty

- **Observed:** At `origin/main` commit `c1f9050ef`, `python3 tools/pcc/pcc.py ledger verify --base origin/main` reports `ledger[3583]: seq is 3535` and `BROKEN`. File line 3583 has `seq=3582`; line 3584 returns to `seq=3535`. `pcc claim new` refuses with the same error. The failed command left an untracked claim file, which was moved outside the checkout to `/Volumes/SSD990-2/m31-orphan-pcc-f2f951.json` without adding it to the ledger.
- **Observed:** The local M31 branch at `56e2a24fb` had 3,586 sequential entries. Both parents of merge `22389cb04` already show the repeated sequence at line 3584; the defect preceded the final merge of PR #1960. Blame attributes the sequence-3535 row to historical commit `1812a0ad0`, but blame does not identify which merge first placed it after sequence 3582.
- **Observed:** `tools/lean/proof-gate.sh experiments/prime-field-auxiliary-ic/m31-full-rust-comparison` passes under the pinned Lean 4.36 project, auditing 11 theorems with zero trusted exceptions. The local axiom auditor self-test passes its expected pass and rejection fixtures after PR #1978's fixes. Existing file-only claim `PCC-20261125-9cbb25` remains unsigned and does not name the Lake project.
- **Derived or proved:** The append-chain invariant fails at the stated row, so appending more entries cannot restore the required contiguous sequence and hash chain. The original independent histories and their exact merge point have not been fully reconstructed.
- **Suspected explanation:** A normal Git merge retained rows from two valid but divergent PCC ledger tails. Confirm this by comparing the relevant merge parents and each tail's hash links before selecting a recovery procedure.
- **Missing capability:** An owner-reviewed ledger reconciliation that preserves both histories as evidence and establishes a valid canonical append chain or an explicit versioned migration accepted by the PCC gate.
- **What this evidence does not establish:** It does not invalidate the Lean kernel result or the archived M31 raw timing files. It does prevent a new signed PCC theorem standing and weakens the repository-wide claim gate until repaired.

## What would unblock it

- [ ] Identify the first merge that joined divergent tails, inventory every distinct claim and verdict from each tail, and retain immutable copies and SHA-256 digests of both histories.
- [ ] Apply an owner-approved ledger recovery or versioned migration without silently discarding records; run `pcc ledger verify --base` on the repaired main and confirm the canonical sequence and hash links.
- [ ] Create a new PCC theorem claim naming the pinned M31 Lake project, then obtain a CI-signed verdict and check `pcc standing` for that exact claim digest.

The first two conditions restore claim custody. The third establishes signed standing for the logical bitmap theorem only; it would not verify Rust refinement or performance.

## Next discriminating step

- **Action or proof obligation:** Read the first-parent ledger history around line 3584, compare the two valid parent tails and their claims, and prepare a reviewed reconciliation plan before any ledger mutation.
- **Inputs and controls:** `origin/main` at `c1f9050ef`, local valid tail at `56e2a24fb`, merge parents around `22389cb04`, `pcc ledger verify`, and a complete claim-ID inventory.
- **Execution limits and stop condition:** Read-only audit until the ledger maintainer approves a concrete migration; do not edit `pcc/ledger.jsonl` by hand or append into a broken chain.
- **Outcomes and next actions:** If both histories can be retained in a valid migration, run the gate and issue the project claim. If hashes or records cannot be reconciled, preserve the fork and escalate the exact missing provenance. If a newer main already repairs the chain, rerun verification and then proceed with the claim.
- **Recheck trigger:** A new main commit affecting `pcc/ledger.jsonl` or an owner-approved recovery plan.

## Resolution and history

2026-11-25: Open. The pinned bitmap Lean project and proof gate pass locally, but the repository ledger rejects a new claim. This record does not repair the ledger or certify the performance result.
