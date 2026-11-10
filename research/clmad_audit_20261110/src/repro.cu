// Reproduction, written independently, of the reported ptxas clmad folding
// defect: a Karatsuba 128x128 carry-less product whose running product starts
// from the constant one.  Build variants:
//   -DN=<steps>        chain length (default 14)
//   -DSCHOOLBOOK       four 64x64 products instead of three (control)
//   -DSQUARE           carry-less squaring chain e = e*e (finding A7)
// Exit 0: every step matches the host; 1: a mismatch; 2: CUDA error.
#include <cuda_runtime.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>

#ifndef N
#    define N 14
#endif

struct U128 {
    uint64_t lo, hi;
};

__device__ __forceinline__ void clmul64(uint64_t a, uint64_t b, uint64_t &lo, uint64_t &hi)
{
    asm("clmad.lo.u64 %0, %1, %2, 0;" : "=l"(lo) : "l"(a), "l"(b));
    asm("clmad.hi.u64 %0, %1, %2, 0;" : "=l"(hi) : "l"(a), "l"(b));
}

// 128x128 carry-less product, 256 bits in p0..p3 (p0 lowest).
__device__ __forceinline__ void mul256(U128 a, U128 b, uint64_t &p0, uint64_t &p1, uint64_t &p2,
                                       uint64_t &p3)
{
    uint64_t l0, l1, h0, h1;
    clmul64(a.lo, b.lo, l0, l1);
    clmul64(a.hi, b.hi, h0, h1);
#ifdef SCHOOLBOOK
    uint64_t x0, x1, y0, y1;
    clmul64(a.lo, b.hi, x0, x1);
    clmul64(a.hi, b.lo, y0, y1);
    const uint64_t m0 = x0 ^ y0, m1 = x1 ^ y1;
#else
    uint64_t m0, m1;
    clmul64(a.lo ^ a.hi, b.lo ^ b.hi, m0, m1);
    m0 ^= l0 ^ h0;
    m1 ^= l1 ^ h1;
#endif
    p0 = l0;
    p1 = l1 ^ m0;
    p2 = h0 ^ m1;
    p3 = h1;
}

// Fold 256 -> 128 by XOR of the high half into the low half.  Not a field
// reduction; the host applies the same fold, so any fixed choice serves.
__device__ __forceinline__ U128 mul128(U128 a, U128 b)
{
    uint64_t p0, p1, p2, p3;
    mul256(a, b, p0, p1, p2, p3);
    U128 r;
    r.lo = p0 ^ p2;
    r.hi = p1 ^ p3;
    return r;
}

__global__ void chain(const U128 *in, U128 *out)
{
    if (threadIdx.x != 0 || blockIdx.x != 0) return;
#ifdef SQUARE
    U128 e = in[0];
#    pragma unroll
    for (int t = 0; t < N; ++t) {
        e = mul128(e, e);
        out[t] = e;
    }
#else
    U128 e;
    e.lo = 1;
    e.hi = 0;
#    pragma unroll
    for (int t = 0; t < N; ++t) {
        e = mul128(e, in[t]);
        out[t] = e;
    }
#endif
}

// Host reference: bitwise carry-less arithmetic, no intrinsics.
static void h_clmul64(uint64_t a, uint64_t b, uint64_t &lo, uint64_t &hi)
{
    lo = 0;
    hi = 0;
    for (int i = 0; i < 64; ++i) {
        if ((b >> i) & 1) {
            lo ^= a << i;
            if (i) hi ^= a >> (64 - i);
        }
    }
}

static U128 h_mul128(U128 a, U128 b)
{
    uint64_t l0, l1, h0, h1, m0, m1;
    h_clmul64(a.lo, b.lo, l0, l1);
    h_clmul64(a.hi, b.hi, h0, h1);
#ifdef SCHOOLBOOK
    uint64_t x0, x1, y0, y1;
    h_clmul64(a.lo, b.hi, x0, x1);
    h_clmul64(a.hi, b.lo, y0, y1);
    m0 = x0 ^ y0;
    m1 = x1 ^ y1;
#else
    h_clmul64(a.lo ^ a.hi, b.lo ^ b.hi, m0, m1);
    m0 ^= l0 ^ h0;
    m1 ^= l1 ^ h1;
#endif
    const uint64_t p0 = l0, p1 = l1 ^ m0, p2 = h0 ^ m1, p3 = h1;
    U128 r;
    r.lo = p0 ^ p2;
    r.hi = p1 ^ p3;
    return r;
}

static uint64_t splitmix64(uint64_t &s)
{
    uint64_t z = (s += 0x9E3779B97F4A7C15ull);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
}

#define CK(x)                                                                                      \
    do {                                                                                           \
        cudaError_t e_ = (x);                                                                      \
        if (e_ != cudaSuccess) {                                                                   \
            printf("cuda error: %s (%s)\n", cudaGetErrorString(e_), #x);                           \
            return 2;                                                                              \
        }                                                                                          \
    } while (0)

int main(int argc, char **argv)
{
    uint64_t seed = argc > 1 ? strtoull(argv[1], nullptr, 0) : 0x243F6A8885A308D3ull;
    std::vector<U128> in(N), out(N), want(N);
    for (int t = 0; t < N; ++t) {
        in[t].lo = splitmix64(seed);
        in[t].hi = splitmix64(seed);
    }
#ifdef SQUARE
    U128 e = in[0];
    for (int t = 0; t < N; ++t) {
        e = h_mul128(e, e);
        want[t] = e;
    }
#else
    U128 e;
    e.lo = 1;
    e.hi = 0;
    for (int t = 0; t < N; ++t) {
        e = h_mul128(e, in[t]);
        want[t] = e;
    }
#endif
    U128 *d_in = nullptr, *d_out = nullptr;
    CK(cudaMalloc(&d_in, sizeof(U128) * N));
    CK(cudaMalloc(&d_out, sizeof(U128) * N));
    CK(cudaMemcpy(d_in, in.data(), sizeof(U128) * N, cudaMemcpyHostToDevice));
    CK(cudaMemset(d_out, 0, sizeof(U128) * N));
    chain<<<1, 32>>>(d_in, d_out);
    CK(cudaGetLastError());
    CK(cudaDeviceSynchronize());
    CK(cudaMemcpy(out.data(), d_out, sizeof(U128) * N, cudaMemcpyDeviceToHost));
    int wrong = 0;
    for (int t = 0; t < N; ++t) {
        if (out[t].lo != want[t].lo || out[t].hi != want[t].hi) {
            if (wrong < 3)
                printf("step %2d: got %016llx %016llx, want %016llx %016llx\n", t,
                       (unsigned long long)out[t].hi, (unsigned long long)out[t].lo,
                       (unsigned long long)want[t].hi, (unsigned long long)want[t].lo);
            ++wrong;
        }
    }
    printf("%d of %d steps wrong\n", wrong, N);
    cudaFree(d_in);
    cudaFree(d_out);
    return wrong ? 1 : 0;
}
