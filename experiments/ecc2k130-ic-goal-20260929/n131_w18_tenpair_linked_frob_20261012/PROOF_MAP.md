# Proof and verification map

| Result | Evidence | Scope |
| --- | --- | --- |
| Linked W18 pair-code source has 18 distinct folded columns on the constructed witness | [Sage audit](sage_fixture_result.json) | All ten exact source masks and their folded columns; slots 0 and 1 repeat only their two columns. |
| A constructed ten-pair assignment satisfies the linked N131 XCNF | [control result](control_result.json) | Full circuit clauses and native XOR rows, including all nine group links and the binary target selector. |
| Constructed signed group sum and subgroup target are correct | [checked Sage source](audit_fixture_sage.py), [audit result](sage_fixture_result.json) | Exact field `GF(2^131)` with polynomial `t^131+t^13+t^2+t+1`, curve `[1,0,0,0,1]`, and subgroup order `680564733841876926932320129493409985129`. |
| Public query reached its declared cap with no terminal solver answer | [query receipt](query_result.json), [solver log](solver.stdout.txt) | One worker, 600-second parent cap, 4-GiB combined RSS cap, 524 target choices. |
| Public formula and terminal receipt replay byte for byte | [terminal audit](audit_result.json), [archive receipt](archive_receipt.json) | Raw XCNF hashes are recoverable from the gzip archives. |

The linked source is implemented as shared selector and reciprocal wires in [ten.py](ten.py). It does not constrain the two signed point choices to agree; the constructed control chooses agreement and checks it through independent group arithmetic. The planned unary-prefix identity is not asserted as a proved theorem here. The coefficient folding identity for repeated Frobenius columns has a checked Lean proof in the prior [linked-pair proof map](../n41_n131_linked_frobenius_pair_20261012/PROOF_MAP.md).
