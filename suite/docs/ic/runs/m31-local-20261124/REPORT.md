# Native m=31 local feasibility results

Producer assertions only: [pcc:unverified]. CPU-only debug build; local runs authorized by the user. No speedup or promotion claim.

Source commit: `6f58ff6d021f95494cb585a09a55ee3e3c2c927c`. Binary SHA256: `0a7ff301978a4a1a3d2fe08cbb0ac2068fb9fe23020e0273eeee3594f42d4d2f`.

Each process had 20 seconds and 2 GiB. SAT calls had a 1000-conflict cap; m31 cells had four target trials.
Native incomplete means the capped pipeline did not recover a logarithm. A timeout has no completed native report; its relation count is unknown, not zero.

| Cell | Process outcome | Relations | Solver capped calls | Native log self-check | Wall s |
|---|---|---:|---:|---|---:|
| n7-seed1-mitm-m2 | ok | 2 | unknown | True | 0.568 |
| n7-seed1-chain-m2 | ok | 2 | 0 | True | 0.669 |
| n7-seed1-chain-m31-serial | native_incomplete | 0 | 4 | False | 8.073 |
| n7-seed1-chain-m31-balanced | native_incomplete | 0 | 4 | False | 6.065 |
| n7-seed2-mitm-m2 | ok | 5 | unknown | True | 0.652 |
| n7-seed2-chain-m2 | ok | 5 | 0 | True | 0.670 |
| n7-seed2-chain-m31-serial | native_incomplete | 0 | 4 | False | 7.530 |
| n7-seed2-chain-m31-balanced | native_incomplete | 0 | 4 | False | 6.523 |
| n13-seed1-mitm-m2 | native_incomplete | 0 | unknown | False | 0.668 |
| n13-seed1-chain-m2 | native_incomplete | 0 | 0 | False | 2.766 |
| n13-seed1-chain-m31-serial | timeout | unknown | unknown | unknown | 20.071 |
| n13-seed1-chain-m31-balanced | timeout | unknown | unknown | unknown | 20.065 |
| n13-seed2-mitm-m2 | native_incomplete | 2 | unknown | False | 0.691 |
| n13-seed2-chain-m2 | native_incomplete | 2 | 0 | False | 6.281 |
| n13-seed2-chain-m31-serial | timeout | unknown | unknown | unknown | 20.062 |
| n13-seed2-chain-m31-balanced | timeout | unknown | unknown | unknown | 20.075 |
| n17-seed1-mitm-m2 | native_incomplete | 1 | unknown | False | 0.668 |
| n17-seed1-chain-m2 | native_incomplete | 1 | 0 | False | 18.064 |
| n17-seed1-chain-m31-serial | timeout | unknown | unknown | unknown | 20.061 |
| n17-seed1-chain-m31-balanced | timeout | unknown | unknown | unknown | 20.058 |
| n17-seed2-mitm-m2 | native_incomplete | 1 | unknown | False | 0.670 |
| n17-seed2-chain-m2 | timeout | unknown | unknown | unknown | 20.104 |
| n17-seed2-chain-m31-serial | timeout | unknown | unknown | unknown | 20.057 |
| n17-seed2-chain-m31-balanced | timeout | unknown | unknown | unknown | 20.050 |

The m2 arms are controls, not matched m31 speed comparisons. Some setup and solver costs are converted using local measured timing; S is not a qualified performance result.
Leaf membership uses the actual native factor base. Every returned row is checked by native group addition. SAT chart UNSAT excludes identity intermediate sums and is not a proof of global non-decomposability.
Raw reports, console logs, commands, source/lock/binary hashes and process statuses are retained locally beside this report. Signed independent PCC validation is absent.
