// Two-class timing of a dependent clmad chain on one GPU, with controls.
// See PROTOCOL.md.  Output: JSON lines, one per launch.
#include <cuda_runtime.h>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>

#ifndef CHAIN
#define CHAIN 2048
#endif

enum Mode { M_LO = 0, M_HI = 1, M_NEG = 2, M_POS = 3 };
static const char *MODE_NAME[] = {"lo", "hi", "neg", "pos"};

__global__ void chain_kernel(const uint64_t *__restrict__ a, const uint64_t *__restrict__ b,
                             uint64_t *__restrict__ out, long long *__restrict__ cyc, int mode)
{
    const int t = blockIdx.x * blockDim.x + threadIdx.x;
    const uint64_t x = a[t], y = b[t];
    uint64_t r = x ^ y ^ 0x5DEECE66Dull;
    __syncthreads();
    const long long t0 = clock64();
    if (mode == M_LO) {
#pragma unroll 16
        for (int i = 0; i < CHAIN; ++i)
            asm volatile("clmad.lo.u64 %0, %1, %2, %0;" : "+l"(r) : "l"(x), "l"(y));
    } else if (mode == M_HI) {
#pragma unroll 16
        for (int i = 0; i < CHAIN; ++i)
            asm volatile("clmad.hi.u64 %0, %1, %2, %0;" : "+l"(r) : "l"(x), "l"(y));
    } else if (mode == M_NEG) {
#pragma unroll 16
        for (int i = 0; i < CHAIN; ++i)
            asm volatile("xor.b64 %0, %0, %1;\n\tadd.u64 %0, %0, %2;" : "+l"(r) : "l"(x), "l"(y));
    } else {
        // Positive control: the inner trip count depends on the operand.
        const int n = 1 + (__popcll(x) & 7);
        for (int i = 0; i < CHAIN / 8; ++i)
            for (int j = 0; j < n; ++j)
                asm volatile("clmad.lo.u64 %0, %1, %2, %0;" : "+l"(r) : "l"(x), "l"(y));
    }
    const long long t1 = clock64();
    out[t] = r;
    cyc[t] = t1 - t0;
}

struct Cls {
    const char *name;
    int kind;
};
// kinds: 0 zero, 1 one, 2 ones, 3 topbit, 4 alt, 5 lowhw, 6 highhw, 7 random_a,
//        8 random_b, 9 fixed_a, 10 fixed_b
static const Cls CLASSES[] = {{"zero", 0},     {"one", 1},      {"ones", 2},     {"topbit", 3},
                              {"alt", 4},      {"lowhw", 5},    {"highhw", 6},   {"random_a", 7},
                              {"random_b", 8}, {"fixed_a", 9},  {"fixed_b", 10}};
static const int NCLS = sizeof(CLASSES) / sizeof(CLASSES[0]);

static uint64_t weight_word(std::mt19937_64 &g, int lo, int hi)
{
    std::uniform_int_distribution<int> w(lo, hi);
    const int k = w(g);
    uint64_t v = 0;
    while (__builtin_popcountll(v) < k) v |= 1ull << (g() & 63);
    return v;
}

static void fill(int kind, int n, std::vector<uint64_t> &a, std::vector<uint64_t> &b,
                 std::mt19937_64 &g, uint64_t fa0, uint64_t fa1, uint64_t fb0, uint64_t fb1)
{
    a.assign(n, 0);
    b.assign(n, 0);
    for (int i = 0; i < n; ++i) {
        switch (kind) {
        case 0: a[i] = 0; b[i] = 0; break;
        case 1: a[i] = 1; b[i] = 1; break;
        case 2: a[i] = ~0ull; b[i] = ~0ull; break;
        case 3: a[i] = 1ull << 63; b[i] = 1ull << 63; break;
        case 4: a[i] = 0xAAAAAAAAAAAAAAAAull; b[i] = 0x5555555555555555ull; break;
        case 5: a[i] = weight_word(g, 1, 4); b[i] = weight_word(g, 1, 4); break;
        case 6: a[i] = ~weight_word(g, 1, 4); b[i] = ~weight_word(g, 1, 4); break;
        case 7:
        case 8: a[i] = g(); b[i] = g(); break;
        case 9: a[i] = fa0; b[i] = fa1; break;
        case 10: a[i] = fb0; b[i] = fb1; break;
        }
    }
}

#define CK(x)                                                                              \
    do {                                                                                   \
        cudaError_t e_ = (x);                                                              \
        if (e_ != cudaSuccess) {                                                           \
            fprintf(stderr, "cuda error: %s (%s)\n", cudaGetErrorString(e_), #x);          \
            return 2;                                                                      \
        }                                                                                  \
    } while (0)

int main(int argc, char **argv)
{
    int reps = 100, blocks = 1, threads = 32, raw = 1;
    uint64_t seed = 20261110;
    const char *outpath = nullptr;
    const char *geometry = "latency";
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--reps")) reps = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--blocks")) blocks = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--threads")) threads = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--seed")) seed = strtoull(argv[++i], nullptr, 0);
        else if (!strcmp(argv[i], "--out")) outpath = argv[++i];
        else if (!strcmp(argv[i], "--raw")) raw = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--geometry")) geometry = argv[++i];
        else if (!strcmp(argv[i], "--blocks-per-sm")) {
            int dev = 0, sms = 0;
            cudaGetDevice(&dev);
            cudaDeviceGetAttribute(&sms, cudaDevAttrMultiProcessorCount, dev);
            blocks = sms * atoi(argv[++i]);
        } else {
            fprintf(stderr, "unknown arg %s\n", argv[i]);
            return 2;
        }
    }
    FILE *fo = outpath ? fopen(outpath, "w") : stdout;
    if (!fo) return 2;
    const int n = blocks * threads;
    std::mt19937_64 g(seed);
    std::mt19937_64 gb(seed ^ 0x9E3779B97F4A7C15ull);  // random_b uses its own stream
    const uint64_t fa0 = g(), fa1 = g(), fb0 = g(), fb1 = g();
    std::vector<uint64_t> a, b, out(n);
    std::vector<long long> cyc(n);
    uint64_t *d_a, *d_b, *d_out;
    long long *d_cyc;
    CK(cudaMalloc(&d_a, 8 * n));
    CK(cudaMalloc(&d_b, 8 * n));
    CK(cudaMalloc(&d_out, 8 * n));
    CK(cudaMalloc(&d_cyc, 8 * n));
    int dev = 0;
    cudaDeviceProp p;
    CK(cudaGetDevice(&dev));
    CK(cudaGetDeviceProperties(&p, dev));
    fprintf(fo, "{\"meta\":{\"device\":\"%s\",\"cc\":\"%d.%d\",\"sms\":%d,\"chain\":%d,\"blocks\":%d,"
                "\"threads\":%d,\"reps\":%d,\"seed\":%llu,\"geometry\":\"%s\"}}\n",
            p.name, p.major, p.minor, p.multiProcessorCount, CHAIN, blocks, threads, reps,
            (unsigned long long)seed, geometry);

    // Schedule: (mode, class) pairs, shuffled within each rep.  3 warm-up launches.
    std::vector<std::pair<int, int>> plan;
    for (int m = 0; m < 4; ++m)
        for (int c = 0; c < NCLS; ++c) plan.push_back({m, c});
    for (int w = 0; w < 3; ++w) {
        fill(7, n, a, b, g, fa0, fa1, fb0, fb1);
        CK(cudaMemcpy(d_a, a.data(), 8 * n, cudaMemcpyHostToDevice));
        CK(cudaMemcpy(d_b, b.data(), 8 * n, cudaMemcpyHostToDevice));
        chain_kernel<<<blocks, threads>>>(d_a, d_b, d_out, d_cyc, M_LO);
        CK(cudaDeviceSynchronize());
    }
    long long ops_per_mode[4] = {CHAIN, CHAIN, CHAIN * 2, 0};
    for (int rep = 0; rep < reps; ++rep) {
        std::shuffle(plan.begin(), plan.end(), g);
        for (auto &pc : plan) {
            const int mode = pc.first, c = pc.second;
            const int kind = CLASSES[c].kind;
            fill(kind, n, a, b, kind == 8 ? gb : g, fa0, fa1, fb0, fb1);
            CK(cudaMemcpy(d_a, a.data(), 8 * n, cudaMemcpyHostToDevice));
            CK(cudaMemcpy(d_b, b.data(), 8 * n, cudaMemcpyHostToDevice));
            chain_kernel<<<blocks, threads>>>(d_a, d_b, d_out, d_cyc, mode);
            CK(cudaGetLastError());
            CK(cudaDeviceSynchronize());
            CK(cudaMemcpy(cyc.data(), d_cyc, 8 * n, cudaMemcpyDeviceToHost));
            CK(cudaMemcpy(out.data(), d_out, 8 * n, cudaMemcpyDeviceToHost));
            std::vector<long long> s(cyc);
            std::sort(s.begin(), s.end());
            uint64_t chk = 0;
            for (int i = 0; i < n; ++i) chk ^= out[i] * 0x9E3779B97F4A7C15ull;
            // Operation count for the positive control is per thread; we report
            // the chain length and let the analysis use cycles per launch.
            fprintf(fo, "{\"rep\":%d,\"mode\":\"%s\",\"class\":\"%s\",\"ops\":%lld,\"min\":%lld,"
                        "\"median\":%lld,\"max\":%lld,\"checksum\":\"%016llx\"",
                    rep, MODE_NAME[mode], CLASSES[c].name, ops_per_mode[mode], s[0], s[n / 2],
                    s[n - 1], (unsigned long long)chk);
            if (raw) {
                fprintf(fo, ",\"cycles\":[");
                for (int i = 0; i < n; ++i) fprintf(fo, "%s%lld", i ? "," : "", cyc[i]);
                fprintf(fo, "]");
            }
            fprintf(fo, "}\n");
        }
        fflush(fo);
    }
    if (outpath) fclose(fo);
    cudaFree(d_a);
    cudaFree(d_b);
    cudaFree(d_out);
    cudaFree(d_cyc);
    return 0;
}
