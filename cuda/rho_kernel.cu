/*
 * rho_kernel.cu - the CUDA kernel for ca_gpu_rho_solve.
 *
 * This translation unit holds device code only: the __global__ entry point
 * (whose body is ca_dev_rho_thread from ca_device.cuh, the same code the
 * host emulator runs) and one C-callable launch shim, because the <<<>>>
 * syntax needs a CUDA compiler.  All resource management lives in
 * src/gpu_cuda.c so that this file compiles with --cuda-device-only.
 *
 * Built by nvcc, or by clang -x cuda, when CMake is configured with
 * -DCA_CUDA=ON.
 */
#include <cuda_runtime.h>

extern "C" {
#include "cryptanalysis/ca_types.h"
#include "ca_device.cuh"
void ca_set_error(const char *fmt, ...);
}

/*
 * One thread owns CA_GPU_W independent walks and shares a single field
 * inversion between them (Montgomery's trick), which is what makes affine
 * curve arithmetic worthwhile on a GPU: the inversion is a 64-step
 * exponentiation, so amortising it over 8 walks cuts the cost per walk
 * step by roughly an order of magnitude.  args is passed by value: it is
 * 128 bytes of read-mostly scalars plus device pointers, so it lands in
 * constant/parameter memory and needs no extra transfer per launch.
 */
__global__ void ca_rho_walk_kernel(ca_gpu_rho_args args)
{
    uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    ca_dev_rho_thread(&args, tid);
}

#ifdef CA_GPU_SMEM_TABLE
/*
 * CA_GPU_SMEM_TABLE (CMake option, default OFF): the same body with the
 * multiplier table (r * 32 bytes, 32 KiB at r = 1024) copied into dynamic
 * shared memory once per block, so the per-step random reads of
 * mult[4*i + j] are shared-memory loads instead of L1/L2 gathers.  Every
 * thread of the block helps copy before any of them may return (threads past
 * nthreads return inside ca_dev_rho_thread, after the barrier).  The walk,
 * the walk ids and the DP output are those of ca_rho_walk_kernel; only the
 * address the table is read from changes.  The trade is occupancy: 32 KiB per
 * block limits a 96 KiB-shared SM (sm_70) to 3 blocks.  Untested on a GPU;
 * the kernel above is kept unchanged (its mangled name is what the Rust
 * binding loads from the build-time PTX).
 */
__global__ void ca_rho_walk_kernel_smem(ca_gpu_rho_args args)
{
    extern __shared__ uint64_t ca_smem_mult[];
    const uint32_t words = 4u * args.r;
    for (uint32_t i = threadIdx.x; i < words; i += blockDim.x) ca_smem_mult[i] = args.mult[i];
    __syncthreads();
    /* A local copy: storing a shared-memory pointer into the by-value
     * parameter itself makes clang's NVPTX backend abort ("Cannot cast
     * between two non-generic address spaces"). */
    ca_gpu_rho_args a = args;
    a.mult = ca_smem_mult;
    ca_dev_rho_thread(&a, blockIdx.x * blockDim.x + threadIdx.x);
}

/* The default per-block shared-memory limit every architecture grants
 * without an opt-in attribute. */
#    define CA_GPU_SMEM_TABLE_MAX 49152u
#endif

extern "C" ca_status ca_gpu_cuda_launch_kernel(const ca_gpu_rho_args *args, unsigned blocks,
                                               unsigned threads_per_block)
{
#ifdef CA_GPU_SMEM_TABLE
    const size_t smem = (size_t)args->r * 4 * sizeof(uint64_t);
    if (smem <= CA_GPU_SMEM_TABLE_MAX)
        ca_rho_walk_kernel_smem<<<blocks, threads_per_block, smem>>>(*args);
    else
#endif
        ca_rho_walk_kernel<<<blocks, threads_per_block>>>(*args);
    cudaError_t e = cudaGetLastError();
    if (e == cudaSuccess) e = cudaDeviceSynchronize();
    if (e != cudaSuccess) {
        ca_set_error("CUDA kernel: %s", cudaGetErrorString(e));
        return CA_ERR_INTERNAL;
    }
    return CA_OK;
}
