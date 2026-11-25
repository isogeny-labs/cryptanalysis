# Native m=31 local feasibility results

Producer assertions only: [pcc:unverified]. CPU-only debug build; local runs authorized by the user. No speedup or promotion claim.

Source commit: `9684c7f10374fd534878cf6dc020450f422528e7`. Binary SHA256: `3d6d605867c239cb506e21f23f83a436bd7b16545acb04e3ef704118d2f6776c`.

Each process had 20 seconds and 2 GiB. SAT calls had a 1000-conflict cap; m31 cells had four target trials.
Native incomplete means the capped pipeline did not recover a logarithm. A timeout has no completed native report; its relation count is unknown, not zero.

| Cell | Process outcome | Relations | Solver capped calls | Native log self-check | Wall s |
|---|---|---:|---:|---|---:|
| n7-seed1-chain-m31-serial | native_incomplete | 0 | 4 | False | 9.568 |
| n7-seed1-chain-m31-balanced | native_incomplete | 0 | 4 | False | 11.613 |
| n7-seed2-chain-m31-serial | native_incomplete | 0 | 4 | False | 12.334 |
| n7-seed2-chain-m31-balanced | native_incomplete | 0 | 4 | False | 17.046 |
| n13-seed1-chain-m31-serial | timeout | unknown | unknown | unknown | 20.051 |
| n13-seed1-chain-m31-balanced | timeout | unknown | unknown | unknown | 20.059 |
| n13-seed2-chain-m31-serial | timeout | unknown | unknown | unknown | 20.058 |
| n13-seed2-chain-m31-balanced | timeout | unknown | unknown | unknown | 20.053 |
| n17-seed1-chain-m31-serial | timeout | unknown | unknown | unknown | 20.056 |
| n17-seed1-chain-m31-balanced | timeout | unknown | unknown | unknown | 20.056 |
| n17-seed2-chain-m31-serial | timeout | unknown | unknown | unknown | 20.052 |
| n17-seed2-chain-m31-balanced | timeout | unknown | unknown | unknown | 20.074 |

The m2 controls are retained in the earlier default-branching run, not repeated here. Some setup and solver costs are converted using local measured timing; S is not a qualified performance result.
Leaf membership uses the actual native factor base. Every returned row is checked by native group addition. SAT chart UNSAT excludes identity intermediate sums and is not a proof of global non-decomposability.
Raw reports, console logs, commands, source/lock/binary hashes and process statuses are retained locally beside this report. Signed independent PCC validation is absent.
