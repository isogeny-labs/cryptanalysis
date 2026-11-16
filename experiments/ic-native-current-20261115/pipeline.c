#include "cryptanalysis/cryptanalysis.h"
#include "ca_internal.h"
#include <inttypes.h>
#include <stdio.h>
#include <sys/resource.h>

static double cpu_now(void)
{
    struct timespec t;
    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &t);
    return (double)t.tv_sec + (double)t.tv_nsec * 1e-9;
}

int main(int argc, char **argv)
{
    if (argc == 2 && !strcmp(argv[1], "--calibration")) {
        ca_mont m;
        ca_mont_init(&m, UINT64_C(18446744073709551557));
        uint64_t v = m.r1, factor = ca_mont_to(&m, 1234567);
        double cpu = cpu_now(), wall = ca_now();
        for (unsigned i = 0; i < 5000000; ++i) v = ca_mont_mul(&m, v, factor);
        wall = ca_now() - wall;
        cpu = cpu_now() - cpu;
        printf("{\"cpu\":%.9g,\"wall\":%.9g,\"checksum\":%" PRIu64 "}\n", cpu, wall, v);
        return 0;
    }
    if (argc < 2 || argc > 5) return 2;
    uint64_t p = strtoull(argv[1], NULL, 10);
    uint64_t g = ca_primitive_root(p);
    uint64_t fixture = argc > 3 ? strtoull(argv[3], NULL, 10) : 0;
    unsigned repeats = argc > 4 ? (unsigned)strtoul(argv[4], NULL, 10) : 1;
    if (!repeats || repeats > 1000) return 2;
    uint64_t exponent =
        (UINT64_C(0x23456789abcd) + fixture * UINT64_C(0x9e3779b97f4a7c15)) % (p - 1);
    uint64_t h = ca_powmod(g, exponent, p);
    ca_ic_params params;
    ca_ic_params_default(&params);
    params.threads = 1;
    params.seed = 12345;
    params.verbose = 1;
    params.method = argc > 2 ? (ca_ic_method)atoi(argv[2]) : CA_IC_LINEAR_SIEVE;
    ca_ic_ctx *ctx = NULL;
    ca_ic_stats stats = {0};
    double cpu_start = cpu_now(), start = ca_now();
    ca_status rc = ca_ic_precompute(p, g, &params, &ctx, &stats);
    double setup = ca_now() - start, setup_cpu = cpu_now() - cpu_start;
    if (rc != CA_OK) {
        fprintf(stderr, "precompute: %d %s\n", rc, ca_last_error());
        return 3;
    }
    uint64_t x = 0;
    typedef struct online_sample {
        double wall, cpu, replay;
        uint64_t tries, scalar;
        int verified;
        long involuntary, voluntary, maxrss;
    } online_sample;
    online_sample *samples = calloc(repeats, sizeof(*samples));
    if (!samples) {
        ca_ic_free(ctx);
        return 5;
    }
    double online = 0, online_cpu = 0, replay = 0;
    uint64_t tries = 0;
    int verified = 1;
    for (unsigned i = 0; i < repeats; ++i) {
        ca_stats st = {0};
        struct rusage before, after;
        getrusage(RUSAGE_SELF, &before);
        cpu_start = cpu_now();
        start = ca_now();
        rc = ca_ic_log(ctx, h, &x, &st);
        samples[i].wall = ca_now() - start;
        samples[i].cpu = cpu_now() - cpu_start;
        getrusage(RUSAGE_SELF, &after);
        samples[i].involuntary = after.ru_nivcsw - before.ru_nivcsw;
        samples[i].voluntary = after.ru_nvcsw - before.ru_nvcsw;
        samples[i].maxrss = after.ru_maxrss;
        samples[i].tries = st.iterations;
        samples[i].scalar = x;
        start = ca_now();
        samples[i].verified = rc == CA_OK && x == exponent && ca_powmod(g, x, p) == h;
        samples[i].replay = ca_now() - start;
        verified &= samples[i].verified;
        online += samples[i].wall;
        online_cpu += samples[i].cpu;
        replay += samples[i].replay;
        tries += st.iterations;
    }
    online /= repeats;
    online_cpu /= repeats;
    replay /= repeats;
    printf("{\"p\":%" PRIu64 ",\"method\":%d,\"fixture\":%" PRIu64 ",\"g\":%" PRIu64
           ",\"h\":%" PRIu64 ",\"x\":%" PRIu64 ","
           "\"setup_wall\":%.9g,\"setup_cpu\":%.9g,\"online_wall\":%.9g,\"online_cpu\":%.9g,"
           "\"independent_replay_wall\":%.9g,\"verified\":%d,\"online_tries\":%" PRIu64 ","
           "\"sieve_wall\":%.9g,\"linalg_wall\":%.9g,\"relations\":%u,\"base_primes\":%u,"
           "\"verified_logs\":%u,\"lanczos_iterations\":%u,\"online_repeats\":%u,\"online_runs\":[",
           p, (int)params.method, fixture, g, h, x, setup, setup_cpu, online, online_cpu, replay,
           verified, tries, stats.sieve_seconds, stats.linalg_seconds, stats.relations,
           stats.factor_base_size, stats.verified_logs, stats.lanczos_iterations, repeats);
    for (unsigned i = 0; i < repeats; ++i) {
        printf("%s{\"repeat\":%u,\"wall\":%.9g,\"cpu\":%.9g,\"tries\":%" PRIu64
               ",\"verified\":%d,\"replay_wall\":%.9g,\"involuntary\":%ld,\"voluntary\":%ld,"
               "\"maxrss_native_units\":%ld,\"x\":%" PRIu64 "}",
               i ? "," : "", i, samples[i].wall, samples[i].cpu, samples[i].tries,
               samples[i].verified, samples[i].replay, samples[i].involuntary, samples[i].voluntary,
               samples[i].maxrss, samples[i].scalar);
    }
    printf("],\"numa_pages\":{");
    uint64_t node_pages[256] = {0};
    FILE *maps = fopen("/proc/self/numa_maps", "r");
    if (maps) {
        char line[4096];
        while (fgets(line, sizeof(line), maps)) {
            if (strstr(line, "file=")) continue;
            char *cursor = line;
            while ((cursor = strstr(cursor, " N"))) {
                char *end;
                unsigned long node = strtoul(cursor + 2, &end, 10);
                if (end != cursor + 2 && *end == '=' && node < 256)
                    node_pages[node] += strtoull(end + 1, NULL, 10);
                cursor += 2;
            }
        }
        fclose(maps);
    }
    int first_node = 1;
    for (unsigned i = 0; i < 256; ++i)
        if (node_pages[i]) {
            printf("%s\"%u\":%" PRIu64, first_node ? "" : ",", i, node_pages[i]);
            first_node = 0;
        }
    printf("}}\n");
    free(samples);
    ca_ic_free(ctx);
    return verified ? 0 : 4;
}
