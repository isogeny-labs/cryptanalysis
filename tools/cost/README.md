# tools/cost

Instruction-cost ledgers: a JSON statement of a per-unit cost as a sum of
stage rows, plus the claim it supports.

```sh
python3 tools/cost/ledger.py check tools/cost/examples/*.json
python3 tools/cost/ledger.py template > my-ledger.json
python3 tools/cost/test_ledger.py
make cost-check
```

The contract — units, exhaustive and disjoint rows, normalization, deltas,
break-even fan-outs, `log2` improvements, and "least value at or above"
claim rounding — is in
[docs/INSTRUCTION-COST-ACCOUNTING.md](../../docs/INSTRUCTION-COST-ACCOUNTING.md).
A worked application to the rho walk, including the tunings it ruled out, is in
[docs/RHO-WALK-COST.md](../../docs/RHO-WALK-COST.md).

Standard library only, Python 3.9+.
