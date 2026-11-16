# Three-limb binary-field arithmetic candidate

The feature f2m-karatsuba3 specializes the unreduced 3-by-3 limb product to
six carryless products and XOR coefficient reconstruction, in the existing
PCLMUL/PMULL dispatch. It preserves XOR accumulation and leaves other widths,
reduction and default feature selection unchanged. It applies to binary-field
arithmetic used by ECC and relation code; no full attack gain is established.

The isolated validation crate imports the actual field module and all its
existing tests. Its dependency versions and checksums are pinned by Cargo.lock.
The additional test compares every 192-by-192 pair of basis-bit inputs and
1024 random pairs to an independent bit-shift/XOR reference, with arbitrary
initial output and a sentinel seventh word. Zero and all-ones inputs are also
checked. Native ARM execution reports all17 tests passing with the feature;
Linux validation006 also reports 16 default and17 specialized field tests
passing. Full-suite integration remains pending.
[pcc:unverified]

Claim PCC-20261116-fff2e4 records the producer statement.

No timing has run. Publish this source before allocating any performance
record. Freeze the exact source/binary revisions, hardware dispatch, fields
131/155/163/191 plus two- and four-limb controls, seeds, paired randomized
orders, warm-up and operation accounting before a measurement. Include
field multiply, square/invert and a fixed relation workload, with setup and
online work separate. Use the repository CPU host/placement/noise gates and
retain all regressions. Kernel instruction counts alone do not establish an
end-to-end improvement or novelty. Default activation requires evidence. [pcc:unverified]

Reproduce correctness with cargo test --locked --manifest-path
experiments/ic-f2m-three-limb-20261115/Cargo.toml --features f2m-karatsuba3.
The companion invocation without --features tests the existing default path.
