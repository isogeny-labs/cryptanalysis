# N83 packed root index: reversible-prefix comparison

This experiment compares three exact root-index layouts on the same Q1325
factor base, sampled index states, and one public target: the E-1 open-addressed
hash table, its 18-byte sorted packed records with a 20-bit prefix directory,
and the same packed records sorted by the 83-bit reversal of each canonical
root key. Bit reversal is a bijection, so an equal key and its first inserted
witness remain equal and first after transformation. The change only selects
which key bits form the directory prefix.

The [protocol](protocol.json) fixes nine calls in a balanced three-order
sequence, three per layout, with 2,000,000 sampled pair states, a 1,024 MiB
peak-RSS cap, one target orientation per state, 4,096-state S3 windows and a
180-second process cap for each call. [The workload](workload.json) fixes
the target point, index-state permutation, exact representative-set digest,
and target-independent cache boundary. The stage source, runner, Cargo
manifest/lock and source-tree digests are pinned before execution. Calls
produce exclusive first-attempt records. The runner rejects changed sealed
inputs and checks equal state/root counts, first-witness lookup samples,
arithmetic operations, and target outcomes across all layouts.

The source field representation is GF(2^83) with modulus
`z^83 + z^7 + z^4 + z^2 + 1`, as specified by the frozen Q1325 parent.
It differs from the primary retained-base sweep's polynomial representation
`z^83 + z^45 + z^2 + z + 1`; results require an explicit basis conversion
before application to that exact candidate. `candidate_id` and online
speedup remain null until a complete method, natural relation/rank evidence,
and a verified same-point IC/rho pair are available.

Prepare and commit the inputs before a measurement:

```sh
python3 run.py --prepare
```

Then run the sealed comparison on a fresh copy of this directory:

```sh
python3 run.py --run
```

The measured table and independent audit are added after all first-attempt
calls complete. CPU wall times without a Tier 1 or Tier 0 envelope are stage
diagnostics.
