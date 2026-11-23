# Public M31 batch inversion on Apple M4 Pro

The four arms share the field multiplication, product tree, and C API from commit
`e56e9d034`. The default uses bit reversal on a subgroup of order 62. The
other three share the projection to order 2,046 and differ in reciprocal lookup.
The raw graph uses 16 KiB of labels and the signed graph uses 8 KiB.
Both access memory at addresses derived from public field inputs.

On the M4 Pro with Apple clang 21.0.0, the median paired default/raw wall-time
ratio was 1.421 at one input per call, 1.397 at four, 1.243 at sixteen,
1.044 at 64, and 0.996 at 65,539. Each timed native loop traverses distinct
batches in one deterministic stream. All arms revisit that stream between
rounds. These are warmed batch-inversion measurements on one host.

From this directory, run in an empty output directory:

```sh
bench=$PWD
cd "$(mktemp -d)"
python3 "$bench/build.py"
python3 "$bench/measure.py"
```

The CSV columns for the four arms contain total nanoseconds for the stated
number of calls. The harness rotates the order of the four arms, discards four
warm-up rounds and saves 24 paired rounds at each size. It checks every output
against Python modular exponentiation after each timed loop. The Lean proof
in the parent directory establishes the field identities for the two lookups.
