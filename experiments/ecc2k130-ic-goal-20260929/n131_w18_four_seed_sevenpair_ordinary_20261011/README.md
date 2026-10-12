# Frozen seven-pair N131 ordinary-point query

The [protocol](protocol.json) fixes the same exact N131 public subgroup point
and workload as the one-seed eight-pair all-fiber query. It selects seven W18
pair slots with affine seeds `212..215`, all four raw fibers, and the same
32 signed terminal states. Its source-count ceiling and full mixed-seed
constructed control have passed their separate exact checks; this directory
is the ordinary unpinned search gate.

The [runner](query.py) loads reusable source support and terminal inputs
before the online interval. It then derives the public point's four raw
preimages, constructs all 128 target residuals, builds and writes the exact
XCNF, and launches one CryptoMiniSat worker. The frozen limits are 300
solver CPU seconds, 4,500 total target-dependent wall seconds, and 4 GiB
sampled combined RSS. Each target-dependent phase and the terminal status
will be retained in `query_result.json`; solver stdout and stderr remain
separate. A returned assignment will be decoded for independent group-sum
and folded-column replay before it contributes a relation row.

The protocol was frozen before the ordinary solver run. Save
`./sage --runtime-info` to `sage_runtime_info.json` immediately before
launch, then run through the repository's checked launcher:

```sh
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w18_four_seed_sevenpair_ordinary_20261011/query.py query
```

After the solver process terminates, archive the raw XCNF with
`python3 -B audit.py archive`, replay the 128 residuals and any returned
group witness with `./sage -python audit_sage.py`, then run
`python3 -B audit.py audit`. Keep the raw solver stdout and stderr and the
terminal status even when the cap stops search. Once byte replay passes, the
raw XCNF may be removed; its compressed archive and digest remain in the
receipt.

This proposal has `candidate_id: null` while the ordinary-query result,
relation rank, factor logs, target scalar, and paired same-point rho
measurement are pending.
