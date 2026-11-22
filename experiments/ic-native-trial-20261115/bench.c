/* Compile against the production kernel and a frozen pre-change reference. */
#include "../../src/indexcalc.c"
#include "reference.h"
#include <inttypes.h>

static volatile uint64_t sink;

static double thread_seconds(void)
{
    struct timespec t;
    clock_gettime(CLOCK_THREAD_CPUTIME_ID, &t);
    return (double)t.tv_sec + (double)t.tv_nsec * 1e-9;
}

static uint64_t batch(const uint64_t *inputs, size_t n, const uint32_t *fb,
                      const ca_ic_divisor *div, uint32_t nfb, int optimized)
{
    uint64_t sum = 0;
    for (size_t i = 0; i < n; ++i) {
        relation r;
        uint32_t count = 0;
        int ok = optimized ? trial_factor(inputs[i], fb, div, nfb, 7, &r, &count)
                           : trial_factor_reference(inputs[i], fb, nfb, 7, &r, &count);
        sum += (uint64_t)ok + count;
        for (uint32_t j = 0; j < count; ++j) sum += r.col[j] + (uint32_t)r.val[j];
    }
    sink = sum;
    return sum;
}

int main(void)
{
    enum { N = 65536, REPEATS = 9, BATCHES = 4 };
    const unsigned widths[] = {32, 48, 64, 48};
    const uint32_t bounds[] = {250, 2000, 13000, 2000};
    uint64_t *inputs = malloc(N * sizeof(*inputs));
    uint32_t fb[1600];
    ca_ic_divisor div[1600];
    if (!inputs) return 1;
    ca_rng rng;
    ca_rng_seed(&rng, 0x1c20261115ULL);
    for (unsigned w = 0; w < 4; ++w) {
        uint32_t nfb = (uint32_t)ca_sieve_primes(bounds[w], fb, 1600);
        if (nfb > 1600) return 1;
        double setup = ca_now();
        for (uint32_t j = 0; j < nfb; ++j) div[j] = ca_ic_divisor_init(fb[j]);
        setup = ca_now() - setup;
        uint64_t mask = UINT64_MAX >> (64 - widths[w]);
        for (size_t i = 0; i < N; ++i) {
            uint64_t v = ca_rng_next(&rng) & mask;
            if (w == 3) {
                v = 1;
                /* Smooth products near the same 48-bit ceiling. */
                for (unsigned k = 0; k < 64; ++k) {
                    uint32_t q = fb[ca_rng_below(&rng, nfb)];
                    if (v > mask / q) break;
                    v *= q;
                }
            }
            inputs[i] = v;
        }
        uint64_t verified = 0;
        for (size_t i = 0; i < N; ++i) {
            /* Also exercise offsets and full/near-full relation buffers. */
            for (unsigned mode = 0; mode < 3; ++mode) {
                relation a = {0}, b = {0};
                uint32_t na = mode ? IC_MAX_REL_COLS - (mode == 1) : 0, nb = na;
                int ra = trial_factor_reference(inputs[i], fb, nfb, 7, &a, &na);
                int rb = trial_factor(inputs[i], fb, div, nfb, 7, &b, &nb);
                if (ra != rb || na != nb || memcmp(a.col, b.col, sizeof(a.col)) ||
                    memcmp(a.val, b.val, sizeof(a.val))) {
                    fprintf(stderr, "relation mismatch workload=%u input=%zu mode=%u\n", w, i, mode);
                    return 2;
                }
                ++verified;
            }
        }
        uint64_t expected = batch(inputs, N, fb, div, nfb, 0);
        if (expected != batch(inputs, N, fb, div, nfb, 1)) return 3;
        printf("{\"workload\":%u,\"bits\":%u,\"bound\":%u,\"nfb\":%u,"
               "\"kind\":\"%s\",\"verified_relations\":%" PRIu64 ",\"descriptor_bytes\":%zu,"
               "\"descriptor_setup_seconds\":%.9g}\n",
               w, widths[w], bounds[w], nfb, w == 3 ? "smooth_products" : "uniform_words",
               verified, nfb * sizeof(*div), setup);
        for (unsigned r = 0; r < REPEATS; ++r) {
            for (unsigned order = 0; order < 2; ++order) {
                int optimized = (int)((r + order) & 1);
                double start = ca_now();
                double cpu_start = thread_seconds();
                uint64_t checksum = 0;
                for (unsigned k = 0; k < BATCHES; ++k)
                    checksum = batch(inputs, N, fb, div, nfb, optimized);
                double cpu_elapsed = thread_seconds() - cpu_start;
                double elapsed = ca_now() - start;
                if (checksum != expected) return 3;
                printf("{\"workload\":%u,\"repeat\":%u,\"order\":%u,\"optimized\":%d,"
                       "\"inputs\":%d,\"batches\":%d,\"seconds\":%.9g,\"cpu_seconds\":%.9g,\"checksum\":%" PRIu64 "}\n",
                       w, r, order, optimized, N, BATCHES, elapsed, cpu_elapsed, checksum);
            }
        }
    }
    free(inputs);
    return 0;
}
