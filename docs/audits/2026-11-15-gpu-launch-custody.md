# GPU launch dimensions and PTX output constraints

Source reviewed: main `66b636486d04018aef499fb1ba92cee414fe1fa4`. This is a software correctness audit, with no timing experiment or device execution. All results below are producer assertions pending independent review. [pcc:unverified]

## Launch dimensions

`gpu_rho_solve` computed explicit `blocks * threads_per_block` in 64 bits but converted the result into `a.nthreads` without a range check. The kernel subsequently computes walk IDs in 32 bits as `tid * CA_GPU_W + k`. A thread count can therefore truncate even before a per-walk buffer is allocated, and a count that fits 32 bits can still overflow its walk IDs.

The new guard checks the wide count before conversion against both `UINT32_MAX / CA_GPU_W` and the host capacity for the largest per-walk allocation, `SIZE_MAX / CA_GPU_W / CA_GPU_AUX / sizeof(uint64_t)`. An oversized launch returns `CA_ERR_INVALID` before allocation. Automatic dimensions and ordinary explicit configurations keep their existing behavior.

Four emulator API controls cover these explicit `(blocks, threads_per_block)` pairs:

| Blocks | Threads per block | Failure mode checked |
|---:|---:|---|
| 33,554,432 | 128 | thread count truncates to zero |
| 33,554,433 | 128 | thread count truncates to 128 |
| 4,194,304 | 128 | thread count fits but walk IDs overflow |
| 4,294,967,295 | 4,294,967,295 | wide product exceeds the representable launch |

Each uses an explicit one-step launch and one-operation work limit; it must return `CA_ERR_INVALID` without changing the caller's result word. The initial unguarded run failed all four return-status assertions. The regression returns immediately after the first failed status assertion so a faulty guard cannot proceed to the larger allocation requests.

The complete Debug CTest run with AddressSanitizer and UndefinedBehaviorSanitizer passes all 19 tests (149.84 seconds); the focused GPU test also passes separately. These are local software controls.

## PTX compiler contract

The optional `CA_GPU_PTX_MONT` final subtraction is three instructions in one inline assembly block. Ordinary output constraints permit an output to share a register with an input under the assumption that inputs are consumed first. Here, writing the low result can occur before the high modulus input is consumed. Outputs now carry the early-clobber modifier, matching the earlier multi-instruction multiplication block.

An exact legal-allocation counterexample is `p = 0xffffffffffffffc5`, `t = p + 1`. The expected final residue is one. If `s0` shares the register holding `p1`, the first subtraction overwrites that input with one; the next subtraction produces `0xfffffffe00000001` instead. This demonstrates a declaration hazard, not an observed GPU failure. The compiler used below chose separate virtual registers even for the old declaration.

Both original and corrected extracted function bodies compile with installed LLVM 23.1.1 for `sm_70`, `sm_80`, `sm_89`, and `sm_90`, at `-O0` and `-O3`. Emitted PTX is identical in all eight comparisons. The compile fixture uses the unchanged production arithmetic body plus scalar typedefs and a single kernel caller, without a CUDA runtime dependency. No cubin assembly, NVCC comparison, occupancy measurement, or GPU execution was performed. The optional path remains off by default.

The portable host emulator does not execute the PTX branch. Its sanitizer controls therefore cover the launch guard and shared portable arithmetic, while the extracted-device compile covers acceptance of the revised constraints. Neither substitutes for execution of the optional path on hardware.

Sources: [GCC extended assembly output constraints](https://gcc.gnu.org/onlinedocs/gcc/Extended-Asm.html), [NVIDIA inline PTX assembly](https://docs.nvidia.com/cuda/inline-ptx-assembly/index.html).

Local diagnostics retained under the task-owned CI audit evidence directory include the initial four failed assertions, sanitizer build and CTest logs, extracted original/corrected functions, the legal-overlap integer model, and the eight compiler comparisons. Historical experiment records and source pins are unchanged.
