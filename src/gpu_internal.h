/*
 * gpu_internal.h - backend interface between the generic GPU rho driver
 * (gpu_rho.c) and the CUDA / emulator backends.
 */
#ifndef CA_GPU_INTERNAL_H
#define CA_GPU_INTERNAL_H

#include "cryptanalysis/ca_gpu.h"
#include "../cuda/ca_device.cuh"

/* Twice the expected distinguished points plus slack, saturated before any
 * narrowing. Validated walk IDs and steps are each at most UINT32_MAX, so
 * their product fits uint64_t. dp_bits is clamped to [0, 63] by the driver. */
static inline uint32_t ca_gpu_dp_capacity(uint32_t nwalks, uint32_t steps, uint32_t dp_bits)
{
    const uint32_t limit = 1u << 20, slack = 4096;
    uint64_t work = (uint64_t)nwalks * steps;
    uint64_t twice_expected;
    if (dp_bits == 0) {
        if (work >= (limit - slack) / 2) return limit;
        twice_expected = work * 2;
    } else {
        twice_expected = work >> (dp_bits - 1);
    }
    return twice_expected >= limit - slack ? limit : (uint32_t)twice_expected + slack;
}

/* Existing checkpoint wire layout, shared with format controls. */
typedef struct gpu_rho_checkpoint_header {
    char magic[8];
    uint64_t p, a, b, order, cofactor, base[4], target[4];
    uint32_t kind, negmap, r, nthreads, dp_bits, tpb, requested_steps;
    uint32_t walks_per_thread, aux_words, entry_size, resolved_steps;
    uint64_t seed, resumes, ops, launches, dps, restarts, entries, result;
    double elapsed_seconds;
    uint32_t solved;
    uint64_t checksum;
} gpu_rho_checkpoint_header;

typedef struct ca_gpu_backend_ops {
    const char *name;
    /* Allocate device resources for args (host pointers in args->mult
     * point at host memory; the backend copies them where it needs them).
     * nwalks = args->nthreads * CA_GPU_W. */
    ca_status (*create)(const ca_gpu_rho_args *args, uint32_t threads_per_block, int device,
                        void **ctx);
    /* Run one launch of args->steps steps for every thread; afterwards
     * *dps points to a host buffer with *count DP records (4 words each,
     * clamped to dp_cap) valid until the next call. */
    ca_status (*launch)(void *ctx, const uint64_t **dps, uint32_t *count);
    /* Ask the backend to re-seed walk `wid` at the start of the next launch. */
    void (*restart)(void *ctx, uint32_t wid);
    void (*destroy)(void *ctx);
} ca_gpu_backend_ops;

extern const ca_gpu_backend_ops ca_gpu_emulate_ops;
/* Provided by cuda/rho_kernel.cu when CA_CUDA is on, by gpu_cuda_stub.c otherwise. */
extern const ca_gpu_backend_ops ca_gpu_cuda_ops;
int ca_gpu_cuda_device_count_impl(void);
int ca_gpu_cuda_device_name_impl(int device, char *buf, size_t len);

#endif
