# N83 split-slot root hash

The [nine-call result](RESULT.md) preserves exact first-witness semantics
while reducing table allocation by one-third. Local target-stage medians
were within 4.5 ms for the split slot and separate hash.

This experiment compares three open-addressed layouts on the same Q1325
N83 root-index stream: separate 16-byte keys and 8-byte values, one packed
`u128` slot, and one 16-byte slot split into two `u64` halves. The split
slot's high half contains the 19 high key bits and a 45-bit first-witness
descriptor. Its all-ones value is outside the valid shift range and marks
an empty slot; a miss can stop after reading that half. The low half holds
the remaining 64 key bits. All three layouts use the same hash function,
load-factor rule, insertion order and exact first-witness policy.

The [protocol](protocol.json) fixes nine calls, three per layout, in a
balanced order. Each call uses 2,000,000 sampled pair states, the same
public point and one orientation per state, a 1,024 MiB peak-RSS cap,
4,096-state S3 windows and a 180-second process cap. The
[workload](workload.json) fixes the Q1325 factor-base digest, exact N83
field representation, target point and coprime state permutation. The
field modulus is `z^83+z^7+z^4+z²+1`, distinct from the primary retained
base sweep's polynomial basis.

Five release unit tests check S3 root arithmetic, first-witness equivalence,
duplicate keys, widened sorted prefixes and maximum exact key/descriptor
encodings. The runner verifies hashes of its source, the Cargo files, parent
inputs and crypto library source tree before execution. It compares lookup
samples, state/root counts, operation counts and target outcomes across
all nine first-attempt calls.

The host's default Rust temporary directory on SSD990 filled during the
first preseal test build, before the test binary ran. The same tests passed
with `TMPDIR` set to SSD990-2; the experiment runner records that build
setting. No benchmark call was made before the protocol seal.

Prepare, commit and push the inputs before execution:

```sh
python3 run.py --prepare
```

Then run against the committed protocol with a writable temporary directory:

```sh
TMPDIR=/Volumes/SSD990-2/tmp/n83-split-slot-rusttmp python3 run.py --run
```

This panel measures a bounded root-index stage. `candidate_id` and the
complete single-target online IC/rho ratio remain null until all pipeline
stages are measured and verified in a qualified tier.
