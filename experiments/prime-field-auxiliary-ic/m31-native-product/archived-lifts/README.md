# Batched canonical ordinates on the archived M31 public basis

The depth-five auxiliary chain supplies exactly 32 coordinates. lift.c
evaluates the public curve cubic at all 32, squares each result 29 times
to obtain a root candidate, then checks its square. A successful slot
holds the smaller canonical ordinate. A failed slot holds 2147483647.
Ordinate.lean proves the root choice and the missing-point sentinel
for all field elements, including zero. The kernel uses the same
m31_products implementation as the existing native product benchmark.

The lift comparison charges Python input/output marshalling, point-list
construction, and the FFI call. The complete preparation comparison additionally
runs the hash-pinned archived chain construction, including all its original
checks, from scratch for every call. Library loading, imports and fixture
loading precede the panel. Each observed block checks its returned list in
order. On the 32 archive inputs the list reproduces all 17 manifest points;
128 further batches compare both native builds against Python.

On one shared Apple M4 Pro, median paired wall ratios for Python/NEON were
12.655 for the lift alone and 1.169 for complete basis preparation. NEON
won 24/24 and 17/24 respective blocks. The portable-native/NEON ratios
were 1.055 and 0.994. Thus native compilation accounts for most of the
observed lift gain. The portable build allows normal compiler optimizations.
All six arm orders occur four times in timings.csv. Each block times 64 lift
calls or 12 full preparations. These measurements cover the public basis
stage of the archived workload. Collection and linear algebra are outside
the timed region.

Replay from this directory with Python 3 and SymPy on an ARM64 Mac:

```sh
out=$(mktemp -d)
clang -O3 -flto -mcpu=native -shared -fPIC lift.c ../product.c -o "$out/neon.so"
clang -O3 -flto -mcpu=native -DM31_PORTABLE -shared -fPIC lift.c ../product.c -o "$out/portable.so"
python3 compare.py "$out"
```

Replay Ordinate.lean in the Lean 4.34.1 mathlib environment.
