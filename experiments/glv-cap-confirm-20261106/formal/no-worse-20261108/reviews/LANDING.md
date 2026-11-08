# Current-main PCC landing record

This additive record explains how the previously reviewed proof packet was
placed after the PCC entry that merged on `main`. The independent reports and
the inspected PDF remain byte-identical to their frozen PR #1445 versions.
Their reviewed source head is `8e8c49b6e50463988710f21c5253172176610fbf`;
the first archival head is `02c16b8a7bea6e917ddb9c94cd77838061e6b74b`.

The landing branch starts from cryptanalysis `main` commit
`63de9d7a45b801163094167d87736d89605bf836`. Its PCC ledger already
contained claim `PCC-20261108-3401d0` at sequence 10, hash
`e32b5c7bba57cee069b2e5901555589b4095a174146a61c80bac1a7451d30db0`.
The existing, byte-identical claim `PCC-20261108-5903ae` was appended with
`tools.pcc.pcc.append_entry` at sequence 11, previous hash equal to that
sequence-10 hash. No existing ledger entry was edited or reordered.

## Exact-source preservation

Compared against the archived PR #1445 branch with `git show`, the Lean
module, binding script, blind card, README, review plan, both independent
attestations, technical report, SVG, inspected PDF, and PCC claim all match
byte for byte. The named Lean module SHA-256 remains
`613d9eb1ca98ee95418984b5dac2b8bfcbcd6b705c20b38289bfc93e90a7f2d6`.
The frozen `analyze.py` and `results.json` retain the source hashes recorded
in the proof README. The review judgments therefore still refer to the same
theorem and source bytes; the only new assertion here is ledger placement.
[pcc:unverified]

## Publication-head local checks

- `python3 .../check_binding.py`: pass, including under `python3 -O`.
- `python3 tools/pcc/pcc.py verify PCC-20261108-5903ae --json`: local `pass`
  for both pinned Lean declarations, with empty reasons.
- `tools/lean/proof-gate.sh --out /var/tmp/glv-cap-current-ledger-gate-20261108
  .../NoWorseLogic.lean`: `PASS`, ten audited declarations, zero failing and
  zero trusted native evaluations. The seven cited named theorems have no
  axioms; a generated structure declaration uses `propext`.
- `python3 tools/pcc/pcc.py ledger verify --base origin/main`: 12 entries,
  chain and prefix checks pass.

The local PCC verification is not a signed verdict. Standing remains
`unverified` until an authorized signer records a verdict on `main`.
[pcc:unverified]
