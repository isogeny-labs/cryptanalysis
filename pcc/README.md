# pcc: proof-carrying claims

Data for `tools/pcc/pcc.py`. The contract is `docs/SABOTAGE_RESISTANCE.md`
(AGENTS.md, "Sabotage is assumed: proof-carrying claims").

- `keyring.json`: public keys that may sign verdicts, and the SHA-256 of every
  trusted execution-proof verifier. The owner edits it; producers never do.
- `ledger.jsonl`: the append-only, hash-chained ledger (genesis, verdicts,
  recorded checkpoint bypasses). `pcc.py ledger verify` checks the chain.
- `claims/`: one `PCC-YYYYMMDD-xxxxxx.json` per claim, created by `pcc.py claim new`.
