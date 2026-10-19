# Certicom CPU, NVIDIA CUDA and Apple Metal solvers

The Rust `icx solve` / `ca-icx solve` interface runs Pollard rho, BSGS and index
calculus on the exact published ECC2-131 and ECCp-131 curves, including the
requested ECC2-130/ECCp-130 aliases. The portable CPU implementation needs no
GPU SDK or driver. These native workers provide NVIDIA CUDA and Apple Metal
backends for the same full-width curves and subgroup orders.

`arithmetic.h` is shared unchanged by CUDA, Metal and explicit host emulation.
It uses five 32-bit limbs for coordinates and scalar tags. The binary field is
the published polynomial basis, including all five reduction terms. The prime
field uses integer modular arithmetic. No Koblitz folding is applied to either
random challenge curve. This is a correctness reference implementation; no GPU
speedup or full public-challenge solution is claimed.

| Method | Device work | Host work |
| --- | --- | --- |
| rho | Parallel independent Floyd walks, point arithmetic, and full-width tag updates. | Seed scheduling, collision solving, restarts and final scalar replay. |
| BSGS | Batched baby points and giant queries, with full-width scalar offsets. | Complete-coordinate lookup tables, interval checks and scalar replay. |
| index calculus | Query scalar multiplications and batched signed-pair point decomposition. | Factor-base lifting, relation verification, full-rank BigUint modular linear algebra, scheduling and final replay. |

## Build

NVIDIA CUDA, on a host with `nvcc` and an NVIDIA driver:

```sh
make -C gpu/certicom cuda ARCH=sm_80
gpu/certicom/certicom_cuda --probe
```

Set `ARCH` to the target GPU architecture. Apple Metal, on macOS with Xcode's
Metal compiler and an available Metal device:

```sh
make -C gpu/certicom metal
gpu/certicom/certicom_metal --probe
```

Keep `certicom.metallib` beside `certicom_metal`. `--device N` selects a device
ordinal. The probe opens the actual device; it fails if none is available.

## Run

After building the Rust release CLI, supply the worker explicitly or install
it beside the CLI. Replace `icx` with `ca-icx` (or `crax icx`) in cryptanalysis.
Use an absolute worker path when running from another directory.

```sh
icx solve ECC2-130 --method bsgs --secret 12345 --interval-width 65536 \
  --backend cpu --json
icx solve ECCp-130 --method rho --challenge --max-iterations 16 \
  --max-restarts 0 --backend cuda --gpu-worker gpu/certicom/certicom_cuda --json
icx solve ECC2-130 --method index-calculus --challenge --max-iterations 4 \
  --backend metal --gpu-worker gpu/certicom/certicom_metal --json
```

Every method supports both curves and both GPU workers. `--backend cpu` is the
default. Explicit `cuda` or `metal` selection fails on missing devices, worker
errors, timeouts or a mismatched backend identity. `--backend auto` discovers
CUDA/Metal workers installed beside the executable and may choose CPU; its
report records the actual backend and the selection reason. It never discovers
host emulation as GPU execution.

`--gpu-batch-size` bounds point batches (default 128, maximum 4096).
`--gpu-rho-walks` chooses parallel walks (default 32, maximum 4096); rho's
iteration and restart limits apply to **each walk**, so aggregate work grows
with this count. `--gpu-timeout-seconds` bounds the entire worker session,
including setup and host work (default 120). The watchdog terminates and reaps
the worker; incomplete algorithm budgets return no scalar. Successful scalars,
IC relation equations and recovered factor-base logs are independently checked
by the Rust CPU implementation.

The JSON `execution` block identifies the actual backend/device and counts
kernel launches, explicit point-add/multiply requests and aggregate Floyd
iterations. Each Floyd iteration performs three point steps; those are counted
under `device_rho_iterations`, separately from explicit addition requests.
Speculative batched point work remains in the device counters even if a target
is found earlier in that batch. Counts are not timing or speedup measurements.

## Correctness checks and hardware qualification

```sh
make -C gpu/certicom host
# Shared device source on CPU, explicitly labelled gpu-emulator:
icx solve ECC2-130 --method bsgs --secret 12345 --interval-width 65536 \
  --backend gpu-emulator --gpu-worker gpu/certicom/certicom_emulator --json

# Actual NVIDIA hardware (use metal and certicom_metal on a Mac):
CERTICOM_TEST_BACKEND=cuda \
CERTICOM_TEST_WORKER="$PWD/gpu/certicom/certicom_cuda" \
  cargo test --release --lib certicom_dlp::device_tests -- --test-threads=1 --nocapture
```

For cryptanalysis add `--manifest-path suite/Cargo.toml` to Cargo commands.
The tests cross-check full-width random point operations against independent
Rust arithmetic, recover constructed rho/BSGS/IC known answers on both exact
curves, exercise the IC relation/LA/descent pipeline, and execute all three
methods against both published Qs under small budgets. They also reject wrong
backend identities, malformed points, wrong curve bindings, dead workers and
timeouts. The rho `Q=-G` and prepared IC fixtures are special correctness
controls, not natural-target cost or relation-yield measurements.

The checked-in CLI integration tests also accept `CERTICOM_TEST_BACKEND` and
`CERTICOM_TEST_WORKER` to run the same assertions through the real release CLI.
CPU and emulation tests do not establish physical GPU execution. The dedicated
`Certicom CPU and GPU correctness` workflow separately cross-checks the device
source and compile-checks CUDA/Metal. Its optional hardware job requires an
existing GPU runner label and runs these tests with explicit CUDA or Metal
selection; a skipped hardware job provides no device-execution evidence.
