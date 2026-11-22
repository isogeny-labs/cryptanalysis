# N83 four-million-state root-index capacity gate

The [four-call result](RESULT.md) shows the exact split slot indexing and
scanning all 4,000,000 states under the sampled 1,024 MiB RSS gate, while
both separate-hash calls stopped at 3,235,840 index states. Raw receipts
and an independent audit are retained in this directory.

This panel tests whether the exact 16-byte split-slot root hash carries
4,000,000 sampled quotient-pair states through a 1,024 MiB process peak-RSS
gate where the separate key/value hash may reach that gate. The two layouts
use identical root arithmetic, hash function, load-factor rule, insertion
order, first-witness policy, public target and coprime state sequence. The
first 2,000,000 states are the same prefix measured in the preceding panel.

The [protocol](protocol.json) fixes four calls in hash, split, split, hash
order, each with a 180-second outer process cap, 4,096-state S3 windows and
one target orientation if index construction completes. The memory gate is
the worker's sampled process peak RSS after each index window; it is not an
OS hard limit. Every observed `memory_cap_exceeded`, timeout and partial
state count must remain a result row. A capped arm is not assigned zero
relation yield or a complete target-stage time. The runner permits the arms
to stop at different state counts and audits each first-attempt status.

The [workload](workload.json) fixes the Q1325 factor-base set, exact field
representation, target point and state permutation. The field modulus is
`z^83+z^7+z^4+z²+1`, distinct from the primary retained-base sweep's
polynomial representation. This is an index capacity test; `candidate_id`
and complete one-target online IC/rho ratio remain null.

The worker source and its five release unit tests are byte-identical to the
audited split-slot panel. The runner hashes that source, its own code,
Cargo files, parent inputs and crypto source tree before execution. The
host's default Rust temporary directory on SSD990 is full; build on
SSD990-2 with the explicit `TMPDIR` shown below.

Prepare, commit and push before any call:

```sh
python3 run.py --prepare
```

Then run the committed protocol:

```sh
TMPDIR=/Volumes/SSD990-2/tmp/n83-split-slot-rusttmp python3 run.py --run
```
