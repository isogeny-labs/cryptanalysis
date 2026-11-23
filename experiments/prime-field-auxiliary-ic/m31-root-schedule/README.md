# Batched checked M31 square roots

The C entry point in [root.h](root.h) accepts canonical residues modulo 2³¹−1 and writes the smaller root or the modulus as a nonsquare sentinel. The AArch64 implementation interleaves eight independent four-lane NEON vectors, applies the existing balanced signed fold to each squaring, and converts the final checked result to canonical form. Partial batches use a zero-padded local tail. Other architectures use the portable implementation. Source and destination can be identical or disjoint. The function allocates no heap memory.

## Native throughput

Local Apple M4 Pro. Each of two processes used 30 blocks of 4096 resident inputs. Block data came from different seeds in the two processes. Each timed arm ran 32 times, with all five positions balanced for each method. Before timing, every arm was compared with modular exponentiation on the entire block. Results were checked again after every timed interval. Buffer setup and any language-level FFI dispatch are outside these measurements. The output-producing call to the public C ABI is inside the timing for arm 4.

| Arm | Method | Seed 1 ns/value | Seed 2 ns/value |
|---:|---|---:|---:|
| 0 | Archived high-multiply checked root | 11.049 | 11.259 |
| 1 | Unsigned minimum fold, one vector | 8.626 | 8.647 |
| 2 | Unsigned minimum fold, eight vectors | 3.362 | 3.366 |
| 3 | Balanced signed fold, one vector | 6.659 | 6.705 |
| 4 | Public C ABI, balanced signed fold, eight vectors | 2.844 | 2.886 |

Relative to arm 0, arm 4 gave median block-paired speedups of 3.882× and 3.898×, winning all 60 comparisons. With the unsigned arithmetic fixed, interleaving eight vectors gave 2.551× and 2.566× over one vector. With eight vectors fixed, signed arithmetic gave 1.180× and 1.174× over the unsigned minimum fold. The panel measures the bulk checked-root operation; collector time and small-batch latency are separate quantities.

## Verification and replay

Run `python3 check.py` to compile the C header, build native and forced-portable shared libraries, and exercise the ABI through Python ctypes, including null/empty, tails, in-place operation and guard words. On AArch64, `python3 run.py 1` and `python3 run.py 2` reproduce the timing protocol. They reuse the control and oracle in the sibling m31-native-root benchmark. The reported measurements are in seed1.csv and seed2.csv.

Checked.lean composes the sibling signed-fold iteration theorem with a proof that the returned minimum is identical for signed and canonical representatives, including −p for zero. From the mathlib project with Lean 4.35.0-rc1, set src to the absolute directory containing this README and run:

    build=$(mktemp -d)
    export src build
    lake env sh -c 'export LEAN_PATH="$build:$LEAN_PATH"; lean -R "$src/../m31-balanced-square" -o "$build/Signed.olean" "$src/../m31-balanced-square/Signed.lean" && lean "$src/Checked.lean"'

The proof covers the arithmetic. The oracle comparisons exercise compiled code and memory handling.
