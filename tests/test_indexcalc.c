#include "test_fixtures.h"
#include <fcntl.h>
#include <stddef.h>
#include <sys/stat.h>
#include <unistd.h>

static void checkpoint_roundtrip(void)
{
    char dir[] = "/tmp/ca-ic-checkpoint-XXXXXX";
    CHECK(mkdtemp(dir) != NULL);
    char journal[256], precomp[280], progress[280];
    snprintf(journal, sizeof(journal), "%s/relations.ckpt", dir);
    snprintf(precomp, sizeof(precomp), "%s.precomp", journal);
    snprintf(progress, sizeof(progress), "%s/progress.json", dir);
    ca_ic_params pr;
    ca_ic_params_default(&pr);
    pr.seed = 7;
    uint64_t x = 0;
    ca_ic_stats st;
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) == CA_OK);
    CHECK_EQ_U64(ca_powmod(2, x, 1000003), 123456);
    CHECK(access(journal, F_OK) == 0);
    CHECK(access(precomp, F_OK) == 0);
    CHECK(access(progress, F_OK) == 0);

    /* The verified precomputation can be loaded without repeating the sieve. */
    x = 0;
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) == CA_OK);
    CHECK_EQ_U64(ca_powmod(2, x, 1000003), 123456);
    CHECK(st.sieve_seconds == 0);

    /* A changed base must never reuse either artifact. */
    CHECK(ca_ic_solve_checkpointed(1000003, 3, 123456, &pr, journal, 1, &x, &st) == CA_ERR_INVALID);

    /* Simulate interruption during the last relation record.  The completed
     * prefix is replayed and the missing sieve unit is recomputed. */
    CHECK(unlink(precomp) == 0);
    struct stat sb;
    CHECK(stat(journal, &sb) == 0);
    int fd = open(journal, O_WRONLY);
    CHECK(fd >= 0);
    if (fd >= 0) {
        CHECK(ftruncate(fd, sb.st_size - 4) == 0);
        close(fd);
    }
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) == CA_OK);
    CHECK_EQ_U64(ca_powmod(2, x, 1000003), 123456);
    CHECK(unlink(precomp) == 0);
    CHECK(ca_ic_solve_checkpointed(1000003, 3, 123456, &pr, journal, 1, &x, &st) == CA_ERR_INVALID);
    unlink(journal);
    unlink(progress);
    rmdir(dir);
}

static void rexp_checkpoint_roundtrip(void)
{
    char dir[] = "/tmp/ca-ic-rexp-checkpoint-XXXXXX";
    CHECK(mkdtemp(dir) != NULL);
    char journal[256], precomp[280], progress[280];
    snprintf(journal, sizeof(journal), "%s/relations.ckpt", dir);
    snprintf(precomp, sizeof(precomp), "%s.precomp", journal);
    snprintf(progress, sizeof(progress), "%s/progress.json", dir);
    ca_ic_params pr;
    ca_ic_params_default(&pr);
    pr.method = CA_IC_RANDOM_EXPONENT;
    pr.seed = 7;
    pr.threads = 2;
    pr.max_relation_tries = 1;
    uint64_t x = 0;
    ca_ic_stats st;
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) ==
          CA_ERR_NOT_FOUND);
    uint64_t saved_tests = st.smooth_tests;
    CHECK(saved_tests > 0);
    CHECK(access(journal, F_OK) == 0);
    CHECK(access(progress, F_OK) == 0);
    pr.max_relation_tries = 0;
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) == CA_OK);
    CHECK_EQ_U64(ca_powmod(2, x, 1000003), 123456);
    CHECK(st.smooth_tests > saved_tests);
    CHECK(access(precomp, F_OK) == 0);
    CHECK(unlink(precomp) == 0);
    pr.seed = 8;
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) ==
          CA_ERR_INVALID);
    pr.seed = 7;
    FILE *damage = fopen(journal, "r+b");
    CHECK(damage != NULL);
    if (damage) {
        CHECK(fseek(damage, -1, SEEK_END) == 0);
        int last = fgetc(damage);
        CHECK(last != EOF);
        CHECK(fseek(damage, -1, SEEK_END) == 0);
        CHECK(fputc(last ^ 0xff, damage) != EOF);
        CHECK(fclose(damage) == 0);
    }
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) ==
          CA_ERR_INVALID);
    unlink(journal); unlink(progress); rmdir(dir);
}

/* ---- relation record formats v1 and v2 (src/indexcalc.c) ----------------
 * Written out here from the format description, independently of the
 * library, so that the tests below check the library against the spec:
 * v1 relations are a native 784-byte struct with 96 fixed slots; v2
 * relations are packed {uint32 n; uint64 rhs; uint32 col[n]; int32 val[n]}. */
typedef struct {
    uint32_t n;
    uint32_t col[96];
    int32_t val[96];
    uint64_t rhs;
} v1_relation;

typedef struct {
    char magic[8];
    uint64_t p, g, zeta;
    uint32_t B, C, nfb, ncols, target, relation_size;
} journal_header;

typedef struct {
    uint32_t marker, index, count;
    uint64_t candidates, checksum;
} journal_record_v1;

typedef struct {
    uint32_t marker, index, count, entries;
    uint64_t candidates, checksum;
} journal_record_v2;

typedef struct {
    char magic[8];
    uint64_t p, g, zeta, seed, tests, generation, fb_hash;
    double elapsed_seconds;
    uint32_t B, C, nfb, ncols, target, threads, relation_size, count;
    uint64_t checksum;
} rexp_header;

static uint64_t fnv(const void *data, size_t n, uint64_t h)
{
    const unsigned char *p = data;
    for (size_t i = 0; i < n; i++) {
        h ^= p[i];
        h *= UINT64_C(1099511628211);
    }
    return h;
}

static unsigned char *slurp(const char *path, size_t *len)
{
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    unsigned char *buf = NULL;
    struct stat sb;
    if (fstat(fileno(f), &sb) == 0 && sb.st_size > 0) {
        buf = malloc((size_t)sb.st_size);
        if (buf && fread(buf, 1, (size_t)sb.st_size, f) != (size_t)sb.st_size) {
            free(buf);
            buf = NULL;
        }
        *len = (size_t)sb.st_size;
    }
    fclose(f);
    return buf;
}

static int spit(const char *path, const void *data, size_t len)
{
    FILE *f = fopen(path, "wb");
    if (!f) return 0;
    int ok = fwrite(data, 1, len, f) == len;
    return fclose(f) == 0 && ok;
}

/* Decode count v2 relations at buf into v1 records; returns bytes used, 0
 * on a malformed payload. */
static size_t v2_to_v1(const unsigned char *buf, size_t len, uint32_t count, v1_relation *out)
{
    size_t at = 0;
    for (uint32_t i = 0; i < count; i++) {
        memset(&out[i], 0, sizeof(out[i]));
        if (len - at < 12) return 0;
        memcpy(&out[i].n, buf + at, 4);
        memcpy(&out[i].rhs, buf + at + 4, 8);
        at += 12;
        uint32_t n = out[i].n;
        if (n > 96 || (len - at) / 8 < n) return 0;
        memcpy(out[i].col, buf + at, (size_t)n * 4);
        memcpy(out[i].val, buf + at + (size_t)n * 4, (size_t)n * 4);
        at += (size_t)n * 8;
    }
    return at;
}

/* Rewrite a v2 sieve journal as the v1 journal the pre-v2 library wrote. */
static int journal_v2_to_v1(const char *path)
{
    size_t len = 0;
    unsigned char *in = slurp(path, &len);
    if (!in || len < sizeof(journal_header)) {
        free(in);
        return 0;
    }
    journal_header h;
    memcpy(&h, in, sizeof(h));
    if (memcmp(h.magic, "CAICJ2", 7) != 0 || h.relation_size != 0) {
        free(in);
        return 0;
    }
    FILE *f = fopen(path, "wb");
    if (!f) {
        free(in);
        return 0;
    }
    memset(h.magic, 0, sizeof(h.magic));
    memcpy(h.magic, "CAICJ1", 6);
    h.relation_size = (uint32_t)sizeof(v1_relation);
    int ok = fwrite(&h, sizeof(h), 1, f) == 1;
    size_t at = sizeof(h);
    while (ok && at < len) {
        journal_record_v2 r2;
        if (len - at < sizeof(r2)) {
            ok = 0;
            break;
        }
        memcpy(&r2, in + at, sizeof(r2));
        at += sizeof(r2);
        size_t plen = (size_t)r2.count * 12 + (size_t)r2.entries * 8;
        if (r2.marker != UINT32_C(0x43493252) || len - at < plen) {
            ok = 0;
            break;
        }
        /* the v2 checksum, recomputed from the spec */
        uint64_t h2 = fnv(&r2.index, 4, UINT64_C(14695981039346656037));
        h2 = fnv(&r2.count, 4, h2);
        h2 = fnv(&r2.entries, 4, h2);
        h2 = fnv(&r2.candidates, 8, h2);
        if (fnv(in + at, plen, h2) != r2.checksum) {
            ok = 0;
            break;
        }
        v1_relation *rels = calloc(r2.count ? r2.count : 1, sizeof(*rels));
        if (!rels || v2_to_v1(in + at, plen, r2.count, rels) != plen) {
            free(rels);
            ok = 0;
            break;
        }
        at += plen;
        journal_record_v1 r1;
        memset(&r1, 0, sizeof(r1));
        r1.marker = UINT32_C(0x43493152);
        r1.index = r2.index;
        r1.count = r2.count;
        r1.candidates = r2.candidates;
        uint64_t hh = fnv(&r1.index, 4, UINT64_C(14695981039346656037));
        hh = fnv(&r1.count, 4, hh);
        hh = fnv(&r1.candidates, 8, hh);
        r1.checksum = fnv(rels, (size_t)r1.count * sizeof(*rels), hh);
        ok = fwrite(&r1, sizeof(r1), 1, f) == 1 &&
             (!r1.count || fwrite(rels, sizeof(*rels), r1.count, f) == r1.count);
        free(rels);
    }
    if (fclose(f) != 0) ok = 0;
    free(in);
    return ok;
}

/* Rewrite a v2 random-exponent snapshot as the v1 snapshot. */
static int rexp_v2_to_v1(const char *path)
{
    size_t len = 0;
    unsigned char *in = slurp(path, &len);
    if (!in || len < sizeof(rexp_header)) {
        free(in);
        return 0;
    }
    rexp_header h;
    memcpy(&h, in, sizeof(h));
    if (memcmp(h.magic, "CAICRX2", 8) != 0 || h.relation_size != 0) {
        free(in);
        return 0;
    }
    v1_relation *rels = calloc(h.count ? h.count : 1, sizeof(*rels));
    int ok = rels && v2_to_v1(in + sizeof(h), len - sizeof(h), h.count, rels) == len - sizeof(h);
    if (ok) {
        memcpy(h.magic, "CAICRX1", 8);
        h.relation_size = (uint32_t)sizeof(v1_relation);
        uint64_t hh = fnv(&h, offsetof(rexp_header, checksum), UINT64_C(14695981039346656037));
        h.checksum = fnv(rels, (size_t)h.count * sizeof(*rels), hh);
        FILE *f = fopen(path, "wb");
        ok = f && fwrite(&h, sizeof(h), 1, f) == 1 &&
             fwrite(rels, sizeof(*rels), h.count, f) == h.count;
        if (f && fclose(f) != 0) ok = 0;
    }
    free(rels);
    free(in);
    return ok;
}

static int file_magic_is(const char *path, const char *magic)
{
    char got[8] = {0};
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    size_t n = fread(got, 1, sizeof(got), f);
    fclose(f);
    return n == sizeof(got) && memcmp(got, magic, strlen(magic) + 1) == 0;
}

/* A v1 journal (the fixed 784-byte records of the pre-v2 library) still
 * resumes, and is rewritten as the v2 journal the run would have written:
 * the same bytes, so the same units, relations and order. */
static void journal_v1_migration(void)
{
    _Static_assert(sizeof(v1_relation) == 784, "v1 relation records are 784 bytes");
    char dir[] = "/tmp/ca-ic-v1-journal-XXXXXX";
    CHECK(mkdtemp(dir) != NULL);
    char journal[256], precomp[280], progress[280];
    snprintf(journal, sizeof(journal), "%s/relations.ckpt", dir);
    snprintf(precomp, sizeof(precomp), "%s.precomp", journal);
    snprintf(progress, sizeof(progress), "%s/progress.json", dir);
    ca_ic_params pr;
    ca_ic_params_default(&pr);
    pr.seed = 7;
    uint64_t x = 0, x0 = 0;
    ca_ic_stats st, st0;
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x0, &st0) == CA_OK);
    CHECK(file_magic_is(journal, "CAICJ2"));
    size_t v2_len = 0;
    unsigned char *v2 = slurp(journal, &v2_len);
    CHECK(v2 != NULL);

    /* complete v1 journal: replayed (no sieve unit left), rewritten as v2 */
    CHECK(unlink(precomp) == 0);
    CHECK(journal_v2_to_v1(journal));
    CHECK(file_magic_is(journal, "CAICJ1"));
    struct stat sb;
    CHECK(stat(journal, &sb) == 0);
    CHECK((size_t)sb.st_size > v2_len);
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) == CA_OK);
    CHECK_EQ_U64(x, x0);
    CHECK_EQ_U64(st.relations, st0.relations);
    CHECK_EQ_U64(st.sieve_candidates, st0.sieve_candidates);
    size_t got_len = 0;
    unsigned char *got = slurp(journal, &got_len);
    CHECK(got != NULL && v2 != NULL && got_len == v2_len && memcmp(got, v2, v2_len) == 0);
    free(got);

    /* v1 journal torn inside its last record: the prefix is replayed and
     * the missing unit recomputed, and the journal is v2 again */
    CHECK(unlink(precomp) == 0);
    CHECK(journal_v2_to_v1(journal));
    CHECK(stat(journal, &sb) == 0);
    int fd = open(journal, O_WRONLY);
    CHECK(fd >= 0);
    if (fd >= 0) {
        CHECK(ftruncate(fd, sb.st_size - 100) == 0);
        close(fd);
    }
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) == CA_OK);
    CHECK_EQ_U64(x, x0);
    CHECK(file_magic_is(journal, "CAICJ2"));
    got = slurp(journal, &got_len);
    CHECK(got != NULL && got_len == v2_len);
    free(got);

    /* a header whose magic and relation_size disagree is neither version */
    CHECK(unlink(precomp) == 0);
    if (v2) {
        journal_header h;
        memcpy(&h, v2, sizeof(h));
        h.magic[5] = '1'; /* "CAICJ1" with relation_size 0 */
        memcpy(v2, &h, sizeof(h));
        CHECK(spit(journal, v2, v2_len));
        CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) ==
              CA_ERR_INVALID);
        h.magic[5] = '2'; /* "CAICJ2" with relation_size 784 */
        h.relation_size = 784;
        memcpy(v2, &h, sizeof(h));
        CHECK(spit(journal, v2, v2_len));
        CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) ==
              CA_ERR_INVALID);
    }
    free(v2);
    unlink(journal);
    unlink(precomp);
    unlink(progress);
    rmdir(dir);
}

/* A v1 random-exponent snapshot still resumes; the next save writes v2. */
static void rexp_v1_migration(void)
{
    char dir[] = "/tmp/ca-ic-v1-rexp-XXXXXX";
    CHECK(mkdtemp(dir) != NULL);
    char journal[256], precomp[280], progress[280];
    snprintf(journal, sizeof(journal), "%s/relations.ckpt", dir);
    snprintf(precomp, sizeof(precomp), "%s.precomp", journal);
    snprintf(progress, sizeof(progress), "%s/progress.json", dir);
    ca_ic_params pr;
    ca_ic_params_default(&pr);
    pr.method = CA_IC_RANDOM_EXPONENT;
    pr.seed = 7;
    pr.threads = 1;
    pr.max_relation_tries = 20;
    uint64_t x = 0;
    ca_ic_stats st;
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) ==
          CA_ERR_NOT_FOUND);
    CHECK(file_magic_is(journal, "CAICRX2"));
    uint64_t saved_tests = st.smooth_tests;
    CHECK(rexp_v2_to_v1(journal));
    CHECK(file_magic_is(journal, "CAICRX1"));
    pr.max_relation_tries = 0;
    CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) == CA_OK);
    CHECK_EQ_U64(ca_powmod(2, x, 1000003), 123456);
    CHECK(st.smooth_tests > saved_tests);
    CHECK(file_magic_is(journal, "CAICRX2"));

    /* a v1 magic over a v2 payload is rejected, not reinterpreted */
    CHECK(unlink(precomp) == 0);
    size_t len = 0;
    unsigned char *buf = slurp(journal, &len);
    CHECK(buf != NULL);
    if (buf) {
        memcpy(buf, "CAICRX1", 8);
        CHECK(spit(journal, buf, len));
        CHECK(ca_ic_solve_checkpointed(1000003, 2, 123456, &pr, journal, 1, &x, &st) ==
              CA_ERR_INVALID);
    }
    free(buf);
    unlink(journal);
    unlink(precomp);
    unlink(progress);
    rmdir(dir);
}

static void run(uint64_t p, ca_ic_method method, uint32_t threads, int nlogs)
{
    ca_ic_params pr;
    ca_ic_params_default(&pr);
    pr.method = method;
    pr.threads = threads;
    pr.seed = 12345;
    ca_ic_ctx *ctx;
    ca_ic_stats st;
    uint64_t g = ca_primitive_root(p);
    ca_status rc = ca_ic_precompute(p, g, &pr, &ctx, &st);
    CHECK(rc == CA_OK);
    if (rc != CA_OK) { fprintf(stderr, "precompute failed for p=%" PRIu64 ": %s (%s)\n", p, ca_status_string(rc), ca_last_error()); return; }
    printf("p=%" PRIu64 " %s thr=%u: fb=%u unknowns=%u rels=%u verified=%u sieve=%.2fs linalg=%.2fs\n",
           p, method == CA_IC_LINEAR_SIEVE ? "lsieve" : "rexp", threads, st.factor_base_size, st.unknowns,
           st.relations, st.verified_logs, st.sieve_seconds, st.linalg_seconds);
    CHECK(st.verified_logs == st.factor_base_size);
    ca_rng rng;
    ca_rng_seed(&rng, p);
    for (int k = 0; k < nlogs; k++) {
        uint64_t x = ca_rng_below(&rng, p - 1);
        uint64_t h = ca_powmod(g, x, p);
        uint64_t got = 0;
        ca_stats s2 = {0};
        rc = ca_ic_log(ctx, h, &got, &s2);
        CHECK(rc == CA_OK);
        CHECK_EQ_U64(got, x);
    }
    /* non-primitive base: g^2 has order (p-1)/2 */
    ca_ic_free(ctx);
    uint64_t g2 = ca_mulmod(g, g, p);
    rc = ca_ic_precompute(p, g2, &pr, &ctx, &st);
    CHECK(rc == CA_OK);
    if (rc == CA_OK) {
        uint64_t x = 777777 % ((p - 1) / 2);
        uint64_t h = ca_powmod(g2, x, p);
        uint64_t got;
        CHECK(ca_ic_log(ctx, h, &got, NULL) == CA_OK);
        CHECK_EQ_U64(got, x);
        /* element outside <g2> (a non-residue) must be rejected */
        uint64_t nr = g;
        CHECK(ca_ic_log(ctx, nr, &got, NULL) != CA_OK);
        ca_ic_free(ctx);
    }
}

int main(void)
{
    checkpoint_roundtrip();
    rexp_checkpoint_roundtrip();
    journal_v1_migration();
    rexp_v1_migration();
    /* small primes with a large prime factor in p-1 (safe primes) and
     * primes with smooth p-1 (Pohlig-Hellman path) */
    run(1000003, CA_IC_LINEAR_SIEVE, 1, 5);           /* 20 bits, p-1 = 2*3*166667 */
    run(1000003, CA_IC_RANDOM_EXPONENT, 1, 5);
    run(2000000579ULL, CA_IC_LINEAR_SIEVE, 2, 5);     /* 31 bits, safe prime */
    run(2000000579ULL, CA_IC_RANDOM_EXPONENT, 2, 3);
    run(1099511627791ULL, CA_IC_LINEAR_SIEVE, 4, 5);  /* 2^40 + 15 */
    /* 48-bit prime */
    run(281474976710597ULL, CA_IC_LINEAR_SIEVE, 4, 5); /* 2^48 - 59 */
    /* p-1 with a squared large prime? use p = 2*q^2+1 form if prime */
    uint64_t q = 16777259, pp = 0; /* q > 2^24 so the Lanczos + Hensel path is used */
    for (uint64_t k = 1; k < 200 && !pp; k++) {
        if (ca_is_prime(2 * k * q * q + 1)) pp = 2 * k * q * q + 1;
    }
    CHECK(pp != 0);
    printf("square case p=%" PRIu64 " (q=%" PRIu64 ")\n", pp, q);
    run(pp, CA_IC_LINEAR_SIEVE, 2, 3);
    /* one-shot API */
    uint64_t x;
    ca_ic_stats st;
    CHECK(ca_ic_solve(1000003, 2, 123456, NULL, &x, &st) == CA_OK);
    CHECK_EQ_U64(ca_powmod(2, x, 1000003), 123456);

    /* Regression: the automatic factor-base bound (60 and up) exceeded a tiny
     * modulus, so a prime q >= p was in the base, reduced to 0 or to another
     * prime's residue, and the logarithms could not be solved. */
    static const uint64_t tiny[] = {7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 53, 59, 61};
    for (size_t i = 0; i < sizeof(tiny) / sizeof(tiny[0]); i++) {
        for (int m = 0; m < 2; m++) {
            uint64_t tp = tiny[i], tg = ca_primitive_root(tp), th = 2 + (i % (tp - 3));
            ca_ic_params tpar;
            ca_ic_params_default(&tpar);
            tpar.seed = 5 + i;
            tpar.method = m ? CA_IC_RANDOM_EXPONENT : CA_IC_LINEAR_SIEVE;
            uint64_t tx = 0;
            ca_status trc = ca_ic_solve(tp, tg, th, &tpar, &tx, NULL);
            CHECK(trc == CA_OK);
            if (trc == CA_OK) CHECK_EQ_U64(ca_powmod(tg, tx, tp), th);
        }
    }
    TEST_MAIN_END();
}
