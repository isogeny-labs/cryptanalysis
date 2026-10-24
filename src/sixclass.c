#include "cryptanalysis/ca_sixclass.h"
#include "ca_internal.h"
#include "dlog_internal.h"

#include <stdlib.h>
#include <string.h>

typedef struct jump { ca_elem point; uint64_t a, b; } jump;
typedef struct dp { uint64_t key, a, b; int used; } dp;
typedef struct state { ca_elem point; uint64_t a, b; } state;

static uint64_t diff(uint64_t a, uint64_t b, uint64_t n)
{ return ca_submod(a, b, n); }

/* Class key |y| and orientation t with u_t = (-1)^sign lambda^j.
 * The minimum x rotation and minimum y sign commute. */
static int class_of(const ca_group *g, const ca_elem *point, uint64_t beta,
                    uint64_t *key, uint32_t *orientation, ca_elem *canonical)
{
    if (ca_group_is_identity(g, point)) return 0;
    uint64_t words[4];
    ca_group_decode(g, words, point);
    uint64_t xx[3] = {words[0], ca_mulmod(words[0], beta, g->p), 0};
    xx[2] = ca_mulmod(xx[1], beta, g->p);
    uint32_t j = 0;
    for (uint32_t k = 1; k < 3; k++) if (xx[k] < xx[j]) j = k;
    uint64_t minus_y = words[1] ? g->p - words[1] : 0;
    uint32_t sign = minus_y < words[1];
    *key = sign ? minus_y : words[1];
    *orientation = j + 3 * sign;
    if (canonical) {
        uint64_t encoded[4] = {xx[j], *key, 0, 0};
        if (!ca_group_encode(g, canonical, encoded)) return 0;
    }
    return 1;
}

static void combine(const ca_group *g, const ca_elem *base, const ca_elem *target,
                    uint64_t a, uint64_t b, ca_elem *out)
{
    ca_elem ga, qb;
    ca_group_mul(g, &ga, base, a, NULL);
    ca_group_mul(g, &qb, target, b, NULL);
    ca_group_op(g, out, &ga, &qb);
}

ca_status ca_sixclass_solve(const ca_group *g, const ca_elem *base,
                            const ca_elem *target, uint64_t seed,
                            uint32_t r, uint32_t dp_bits,
                            uint64_t max_walkers, uint64_t *x,
                            ca_sixclass_stats *stats)
{
    ca_sixclass_stats local = {0};
    if (!stats) stats = &local;
    memset(stats, 0, sizeof(*stats));
    if (!g || !base || !target || !x || g->kind != CA_GROUP_EC ||
        g->endo_kind != 1 || g->aut_order != 6 || !g->order ||
        r < 2 || (r & (r - 1)) || r > 2048 || dp_bits > 24 ||
        !ca_group_is_valid(g, base) || !ca_group_is_valid(g, target))
        return CA_ERR_INVALID;
    uint64_t n = g->order;
    uint64_t beta = ca_mont_from(&g->mont, g->endo_c_mont);
    /* g->endo_lambda belongs to psi(x,y)=(beta*x,-y); the pure
     * x-rotation (beta*x,y) therefore acts as -endo_lambda. */
    uint64_t lambda = n - g->endo_lambda;
    uint64_t l2 = ca_mulmod(lambda, lambda, n);
    uint64_t units[6] = {1, lambda, l2, n - 1, n - lambda, n - l2};
    uint64_t inverse[6] = {1, l2, lambda, n - 1, n - l2, n - lambda};
    if (ca_powmod(beta, 3, g->p) != 1 || ca_powmod(lambda, 3, n) != 1)
        return CA_ERR_INVALID;
    ca_elem check, phi;
    ca_group_mul(g, &check, base, lambda, NULL);
    uint64_t words[4];
    ca_group_decode(g, words, base);
    words[0] = ca_mulmod(words[0], beta, g->p);
    if (!ca_group_encode(g, &phi, words) || !ca_group_equal(g, &check, &phi))
        return CA_ERR_INVALID;
    jump *table = calloc((size_t)r * 6, sizeof(*table));
    if (!table || max_walkers > SIZE_MAX / sizeof(dp)) { free(table); return CA_ERR_NOMEM; }
    dp *seen = calloc((size_t)(max_walkers ? max_walkers : 1), sizeof(*seen));
    if (!seen) { free(table); return CA_ERR_NOMEM; }
    ca_rng rng;
    ca_rng_seed(&rng, seed);
    for (uint32_t h = 0; h < r; h++) {
        uint64_t a = ca_rng_below(&rng, n), b = ca_rng_below(&rng, n);
        ca_elem m;
        combine(g, base, target, a, b, &m);
        if (ca_group_is_identity(g, &m)) { h--; continue; }
        for (uint32_t t = 0; t < 6; t++) {
            jump *j = &table[6 * h + t];
            ca_group_mul(g, &j->point, &m, inverse[t], NULL);
            j->a = ca_mulmod(a, inverse[t], n);
            j->b = ca_mulmod(b, inverse[t], n);
        }
    }
    uint32_t branch_bits = 0;
    while ((1u << branch_bits) < r) branch_bits++;
    uint64_t dp_mask = ((uint64_t)1 << dp_bits) - 1;
    uint64_t trail_cap = (uint64_t)20 << dp_bits;
    ca_status result = CA_ERR_LIMIT;
    for (uint64_t walker = 0; walker < max_walkers; walker++) {
        stats->walkers++;
        state s;
        s.a = ca_rng_below(&rng, n); s.b = ca_rng_below(&rng, n);
        combine(g, base, target, s.a, s.b, &s.point);
        uint64_t recent[64] = {0};
        state recent_states[64];
        uint32_t used = 0;
        for (uint64_t step = 0; step < trail_cap; step++) {
            uint64_t key; uint32_t t; ca_elem canonical;
            if (!class_of(g, &s.point, beta, &key, &t, &canonical)) {
                stats->exceptional++; break;
            }
            stats->class_visits++;
            if (((key >> branch_bits) & dp_mask) == 0) {
                stats->distinguished++;
                uint64_t aa = ca_mulmod(s.a, units[t], n);
                uint64_t bb = ca_mulmod(s.b, units[t], n);
                for (uint64_t k = 0; k < stats->distinguished - 1; k++) {
                    if (!seen[k].used || seen[k].key != key) continue;
                    stats->collisions++;
                    uint64_t den = diff(bb, seen[k].b, n);
                    uint64_t inv = den ? ca_invmod(den, n) : 0;
                    if (!inv) continue;
                    uint64_t cand = ca_mulmod(diff(seen[k].a, aa, n), inv, n);
                    if (ca_verify_log(g, base, target, cand)) {
                        *x = cand; result = CA_OK; goto done;
                    }
                }
                seen[stats->distinguished - 1] = (dp){key, aa, bb, 1};
                break;
            }
            uint32_t repeat_at = used;
            for (uint32_t k = 0; k < used; k++)
                if (recent[k] == key) { repeat_at = k; break; }
            if (repeat_at < used) {
                uint64_t best_key = key;
                state best = s;
                for (uint32_t k = repeat_at; k < used; k++) {
                    if (recent[k] < best_key) {
                        best_key = recent[k];
                        best = recent_states[k];
                    }
                }
                ca_elem doubled;
                ca_group_dbl(g, &doubled, &best.point);
                s.point = doubled;
                s.a = ca_addmod(best.a, best.a, n);
                s.b = ca_addmod(best.b, best.b, n);
                stats->short_cycle_escapes++;
                used = 0;
                continue;
            }
            if (used == 64) {
                memmove(recent, recent + 1, 63 * sizeof(recent[0]));
                memmove(recent_states, recent_states + 1, 63 * sizeof(recent_states[0]));
                used = 63;
            }
            recent[used] = key;
            recent_states[used++] = s;
            jump *j = &table[6 * (key & (r - 1)) + t];
            ca_group_decode(g, words, &s.point);
            uint64_t jwords[4]; ca_group_decode(g, jwords, &j->point);
            if (words[0] == jwords[0]) { stats->exceptional++; break; }
            ca_elem next;
            ca_group_op(g, &next, &s.point, &j->point);
            s.point = next;
            s.a = ca_addmod(s.a, j->a, n);
            s.b = ca_addmod(s.b, j->b, n);
        }
    }
done:
    free(seen); free(table);
    return result;
}
