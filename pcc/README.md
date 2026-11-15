# pcc: proof-carrying claims

Data for `tools/pcc/pcc.py`. The contract is `docs/SABOTAGE_RESISTANCE.md`
(AGENTS.md, "Sabotage is assumed: proof-carrying claims").

- `keyring.json`: public keys that may sign verdicts, and the SHA-256 of every
  trusted execution-proof verifier. The owner edits it; producers never do:
  the gate reads the base branch's copy on a pull request and fails a change
  whose SHA-256 is not the repository variable `PCC_KEYRING_SHA256`.
- `ledger.jsonl`: the append-only, hash-chained ledger (genesis, verdicts,
  recorded checkpoint bypasses). `pcc.py ledger verify` checks the chain.
- `claims/`: one `PCC-YYYYMMDD-xxxxxx.json` per claim, created by `pcc.py claim new`.
