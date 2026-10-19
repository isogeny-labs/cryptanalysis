# N83 reversible-prefix width panel

The [15-call result](RESULT.md) shows a monotone reduction in lookup
comparisons as the directory widens to 23 bits, while target-stage time
retains a cache/memory tradeoff. All raw calls and the independent audit
are archived here.

This panel varies the directory width of the exact 83-bit-reversed packed
root index across 20, 21, 22, and 23 bits, with the open-addressed hash
index as a same-point reference. The key reversal is bijective; the record
format, duplicate-key first-witness order, pair-state stream, target point,
and S3 arithmetic remain fixed. The wider directories use 8, 16, 32, and
64 MiB respectively, plus one final offset, within the frozen 1,024 MiB
peak-RSS cap. The table retains every 18-byte root record.

The [protocol](protocol.json) fixes fifteen calls, three per layout, in a
rotated order; 2,000,000 sampled pair states; one target orientation per
state; 4,096-state S3 windows; and a 180-second process cap per call. The
[workload](workload.json) fixes the Q1325 factor-base digest and public N83
target. The exact field modulus is `z^83+z^7+z^4+z²+1`, distinct from the
primary retained-base sweep's polynomial basis. This is a bounded root-index
stage comparison; `candidate_id` and full online speedup remain null.

The source, runner, Cargo manifest/lock, parent inputs, and crypto library
source tree are hashed in the protocol. Unit tests check the same first
witness for duplicate roots across all widths. The runner rejects changed
sealed inputs and checks all stage invariants across the fifteen calls.

Prepare, commit and push the inputs before a measurement:

```sh
python3 run.py --prepare
```

Then execute on a fresh copy of this directory:

```sh
python3 run.py --run
```

Raw first-attempt receipts and an independent audit are added after the
panel. CPU times require a Tier 1 or Tier 0 envelope before a speedup claim.
