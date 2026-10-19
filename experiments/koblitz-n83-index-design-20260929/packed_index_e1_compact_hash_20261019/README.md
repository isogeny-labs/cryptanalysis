# N83 one-slot compact root hash

This experiment stores each canonical N83 S3 root key and its first-witness
descriptor in one 16-byte open-addressed slot. The low 83 bits hold the
exact root. The high 45 bits hold a state-vector offset below `2^38` and a
seven-bit Frobenius shift below 83. The all-ones word is outside that valid
descriptor range and marks an empty slot. The insertion order, hash function,
load-factor rule and first-witness policy match the separate key/value hash
arm. A third arm uses the 18-byte sorted reversed-key records with a 23-bit
directory from the prior panel.

The [protocol](protocol.json) fixes nine calls, three per layout, in a
balanced order. Every call uses the same Q1325 base, 2,000,000 sampled pair
states, one public target and one orientation per state, a 1,024 MiB peak-RSS
cap, 4,096-state S3 windows and a 180-second process cap. The
[workload](workload.json) fixes the target, factor-base digest and state
permutation. The field modulus is `z^83+z^7+z^4+z²+1`; the primary retained
base sweep uses another polynomial representation.

The source, runner, Cargo manifest/lock, parent inputs and crypto source
tree are hashed before execution. Four release unit tests cover root
arithmetic, duplicate-key witness equivalence, all reversible prefix widths,
and the maximum key/descriptor boundary. The runner rejects changed sealed
inputs and checks state counts, lookup samples, arithmetic operations and
target outcomes across all nine calls.

Prepare, commit and push before execution:

```sh
python3 run.py --prepare
```

Run only against that committed protocol:

```sh
python3 run.py --run
```

This is a bounded root-index stage comparison. `candidate_id` and the
complete one-target online IC/rho ratio remain null until the complete
pipeline is measured and independently verified in a qualified tier.
