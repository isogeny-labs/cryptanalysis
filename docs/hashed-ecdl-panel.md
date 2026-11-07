# Native preparation of the frozen hashed-ECDL comparison panel

The native `hashed-ecdl-panel` binary prepares all 84 public cases from
[the frozen protocol](https://github.com/isogeny-labs/crypto/blob/784b001c021e754b35157ee85638a767287e2ede/research/hashed_ecdl_speed_20261029/PROTOCOL.md).
It performs no solve, timing, profiling, image publication, or remote submission.

| Curve `(p,a,b)` | Full order | Generator | Seeds | Public target scalars |
| --- | --- | --- | --- | --- |
| `(5,2,1)` | 7 | `(0,1)` | 1–10, 101–104 | 1, 5 |
| `(7,0,3)` | 13 | `(1,2)` | 1–10, 101–104 | 1, 11 |
| `(17,2,2)` | 19 | `(5,1)` | 1–10, 101–104 | 1, 17 |

Seeds 1–10 produce 60 development inputs; seeds 101–104 produce 24 holdouts.
The manifest retains three repetitions and at least five A/A and five
interleaved A/B rounds. It does not schedule or execute them. This prime-field
panel does not replace ECC2K-130 or official ECCp-131.

## Preparation and answer separation

Build with the owning repository's manifest:

```sh
# crypto
cargo build --locked --release --manifest-path crates/hashed-ecdl-tensor/Cargo.toml --bin hashed-ecdl-panel
# cryptanalysis (identical preparer source)
cargo build --locked --release --manifest-path bindings/rust/Cargo.toml -p hashed-ecdl-tensor --bin hashed-ecdl-panel
```

For research use, complete and upload the resume checkpoint and pass
`scripts/checkpoint.sh gate` on the authenticated runner first. Then run the
built `hashed-ecdl-panel prepare NEW_DIRECTORY`. The directory must not exist.
Exclusive creation preserves previous evidence. Failed writes leave partial
output; require a successful command exit before using it. Local unit tests
are development checks, not a research execution path.

`problems/*.json` contain public curve parameters, target coordinates, fixture
seeds, and policies. No expected scalar appears in a solver input or its
filename. The separate `manifest.json` maps inputs to expected scalars and full
cardinalities. Pass only an individual problem to the solver. Freeze the
generator commit, binary and generated file hashes in the future run evidence;
checkpoint and upload the inputs before execution. A local directory does not
establish S3 durability or benchmark admission.

Before writing, a separate bounded integer oracle enumerates every affine
point, checks nonsingularity and full cardinality, and exhausts the generator
orbit through the identity. It uses brute-force field inversion and repeated
addition, without the library's curve, primality, tensor or scalar multiplication
code. Tests cross-check every orbit point with the native curve implementation.
These are bounded fixture controls; the independent general audit remains open.

## Explicit policy addendum before execution

Each input fixes two slots, 16 seed trials, 4,096 columns, 2,000,000,000 charged
steps, vector length 2,000,000, and coefficient width 1,000,000 bits. These make
the existing fixture's step allowance and API defaults explicit. The threshold
remains the algorithm's default. Both arms must receive byte-identical inputs.
Exhaustion stays an unsuccessful row; do not change a budget or discard a case.
This addendum does not rewrite the original protocol or historical receipts.

The manifest records `execution: not_run` and null measurements. S3 checkpoint
transport, a digest-pinned native image and authenticated execution remain
prerequisites. The deployed ecbench image is a different workload. Profiling,
phase accounting, admitted matched A/A and A/B measurements, independent replay,
the full audit and both challenge solves remain open. No speedup is established.

## Sources and validation

Before implementation, reviewed the frozen protocol, existing
`hashed-ecdl-tensor/examples/fixture.json`, runner fields, curve/reduction code
and previous optimization receipts. Fixed unique JSON fields follow
[RFC 8259 §4](https://www.rfc-editor.org/rfc/rfc8259#section-4); exclusive creation
follows the [Rust 1.78 API](https://doc.rust-lang.org/1.78.0/std/fs/struct.OpenOptions.html#method.create_new).
No new algorithm or theorem is proposed. Development outputs and actual access
failures are in `hashed-ecdl-panel-validation.txt`; the generator has its own
`hashed-ecdl-panel.sha256`. Historical manifests and reports remain unchanged.
